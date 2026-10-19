"""Persistent accounts and server-verified duel standings for the flow site."""
import hashlib
import hmac
from contextlib import contextmanager
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time


USERNAME = re.compile(r"^[A-Za-z0-9_]{3,20}$")
SESSION_AGE = 60 * 60 * 24 * 30


class AccountStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(mode=0o600, exist_ok=True)
        os.chmod(self.path, 0o600)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    username_key TEXT NOT NULL UNIQUE,
                    salt BLOB NOT NULL,
                    password_hash BLOB NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash BLOB PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    expires_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    result TEXT NOT NULL CHECK(result IN ('You win','AI wins','Draw')),
                    human_grains INTEGER NOT NULL,
                    ai_grains INTEGER NOT NULL,
                    finished_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS matches_user_id ON matches(user_id);
            """)
            # Older results remain valid; extra physics statistics start with new matches.
            columns = {row[1] for row in db.execute('PRAGMA table_info(matches)')}
            for name in ('human_clears', 'ai_clears', 'human_placed', 'ai_placed', 'human_steps', 'ai_steps'):
                if name not in columns:
                    db.execute(f'ALTER TABLE matches ADD COLUMN {name} INTEGER')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=5000")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def password_hash(password, salt):
        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)

    def available(self, username):
        if not USERNAME.fullmatch(username):
            return False
        with self.connect() as db:
            return db.execute("SELECT 1 FROM users WHERE username_key=?", (username.casefold(),)).fetchone() is None

    def signup(self, username, password):
        if not USERNAME.fullmatch(username):
            raise ValueError("Use 3–20 letters, numbers, or underscores for your username.")
        if not 8 <= len(password) <= 128:
            raise ValueError("Use a password between 8 and 128 characters.")
        salt = secrets.token_bytes(16)
        digest = self.password_hash(password, salt)
        with self.connect() as db:
            try:
                cursor = db.execute(
                    "INSERT INTO users(username,username_key,salt,password_hash,created_at) VALUES(?,?,?,?,?)",
                    (username, username.casefold(), salt, digest, int(time.time())),
                )
            except sqlite3.IntegrityError:
                raise ValueError("That username is already taken.") from None
            return cursor.lastrowid

    def login(self, username, password):
        with self.connect() as db:
            row = db.execute(
                "SELECT id,salt,password_hash FROM users WHERE username_key=?",
                (username.casefold(),),
            ).fetchone()
        # Perform the same work when a username is absent.
        salt = row[1] if row else b"\0" * 16
        actual = self.password_hash(password, salt)
        if not row or not hmac.compare_digest(actual, row[2]):
            raise ValueError("Username or password is incorrect.")
        return row[0]

    def create_session(self, user_id):
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute(
                "INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)",
                (hashlib.sha256(token.encode()).digest(), user_id, int(time.time()) + SESSION_AGE),
            )
        return token

    def user_for_token(self, token):
        if not token or len(token) > 128:
            return None
        with self.connect() as db:
            row = db.execute("""
                SELECT users.id,users.username FROM sessions JOIN users ON users.id=sessions.user_id
                WHERE sessions.token_hash=? AND sessions.expires_at>?
            """, (hashlib.sha256(token.encode()).digest(), int(time.time()))).fetchone()
        return {"id": row[0], "username": row[1]} if row else None

    def end_session(self, token):
        if token:
            with self.connect() as db:
                db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).digest(),))

    def record_match(self, match, user_id):
        if not user_id or match.result not in ("You win", "AI wins", "Draw"):
            return
        with self.connect() as db:
            db.execute("""
                INSERT OR IGNORE INTO matches(match_id,user_id,result,human_grains,ai_grains,finished_at,
                                             human_clears,ai_clears,human_placed,ai_placed,human_steps,ai_steps)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (match.id, user_id, match.result, match.stats["human"].grains,
                  match.stats["ai"].grains, int(time.time()),
                  getattr(match.stats['human'], 'clears', None), getattr(match.stats['ai'], 'clears', None),
                  getattr(match.stats['human'], 'placed', None), getattr(match.stats['ai'], 'placed', None),
                  getattr(getattr(match, 'human', None), 'step_count', None),
                  getattr(getattr(match, 'ai', None), 'step_count', None)))

    def standings(self, user_id=None, page=1):
        ranking = """WITH totals AS (
                SELECT users.id,users.username,
                       SUM(CASE WHEN result='You win' THEN 1 ELSE 0 END) wins,
                       SUM(CASE WHEN result='AI wins' THEN 1 ELSE 0 END) losses,
                       SUM(CASE WHEN result='Draw' THEN 1 ELSE 0 END) draws,
                       SUM(human_grains) grains, SUM(ai_grains) ai_grains, users.username_key
                FROM users JOIN matches ON matches.user_id=users.id
                GROUP BY users.id
                ), ranked AS (
                SELECT *, ROW_NUMBER() OVER (ORDER BY (wins-losses) DESC,grains DESC,username_key ASC) rank
                FROM totals)
            """
        def player(row):
            return dict(id=row[0], username=row[1], wins=row[2], losses=row[3], draws=row[4],
                        grains=row[5], ai_grains=row[6], matches=row[2]+row[3]+row[4],
                        difference=row[2]-row[3], rank=row[8])
        with self.connect() as db:
            count, total_matches, total_grains = db.execute('SELECT COUNT(DISTINCT user_id),COUNT(*),COALESCE(SUM(human_grains),0) FROM matches').fetchone()
            pages = max(1, (count + 19) // 20)
            page = min(max(1, page), pages)
            rows = db.execute(ranking + 'SELECT * FROM ranked ORDER BY rank LIMIT 20 OFFSET ?', ((page-1)*20,)).fetchall()
            top = db.execute(ranking + 'SELECT * FROM ranked ORDER BY rank LIMIT 10').fetchall()
            own = db.execute(ranking + 'SELECT * FROM ranked WHERE id=?', (user_id,)).fetchone()
        mine = player(own) if own else None
        if mine:
            mine['top_percent'] = max(1, round(100 * mine['rank'] / count))
        return dict(top=[player(row) for row in top], entries=[player(row) for row in rows], mine=mine,
                    players=count, matches=total_matches, average_grains=total_grains/total_matches if total_matches else 0,
                    page=page, pages=pages, profile=self.match_details(user_id) if user_id else None,
                    community=self.match_details(), totals=self.global_stats())

    def match_details(self, user_id=None):
        where = ' WHERE user_id=?' if user_id is not None else ''
        with self.connect() as db:
            row = db.execute('''SELECT COUNT(*),COALESCE(MAX(human_grains),0),COALESCE(MAX(ai_grains),0),
                AVG(human_grains),AVG(ai_grains),AVG(human_clears),AVG(ai_clears),
                SUM(CASE WHEN human_placed>0 THEN human_grains END),SUM(human_placed),
                SUM(CASE WHEN ai_placed>0 THEN ai_grains END),SUM(ai_placed),AVG(human_steps),AVG(ai_steps),COUNT(human_placed)
                FROM matches''' + where, (user_id,) if user_id is not None else ()).fetchone()
        return dict(matches=row[0], best_human=row[1], best_ai=row[2], human_average=row[3], ai_average=row[4],
                    human_clears=row[5], ai_clears=row[6], human_efficiency=row[7]/row[8] if row[8] else None,
                    ai_efficiency=row[9]/row[10] if row[10] else None, human_steps=row[11], ai_steps=row[12],
                    detailed_matches=row[13])

    def global_stats(self):
        with self.connect() as db:
            row = db.execute("""
                SELECT COUNT(*),
                       COALESCE(SUM(CASE WHEN result='You win' THEN 1 ELSE 0 END),0),
                       COALESCE(SUM(CASE WHEN result='AI wins' THEN 1 ELSE 0 END),0),
                       COALESCE(SUM(CASE WHEN result='Draw' THEN 1 ELSE 0 END),0),
                       COALESCE(SUM(human_grains),0),COALESCE(SUM(ai_grains),0)
                FROM matches
            """).fetchone()
        count, human_wins, ai_wins, draws, human_grains, ai_grains = row
        return dict(matches=count, human_wins=human_wins, ai_wins=ai_wins,
                    draws=draws, human_grains=human_grains, ai_grains=ai_grains)
