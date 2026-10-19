import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

from web_accounts import AccountStore


class StandingsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'accounts.sqlite3'
        self.store = AccountStore(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def add_player(self, username):
        with self.store.connect() as db:
            return db.execute('INSERT INTO users(username,username_key,salt,password_hash,created_at) VALUES(?,?,?,?,0)',
                              (username, username.casefold(), b'salt', b'hash')).lastrowid

    def match(self, match_id, grains, result='You win'):
        return SimpleNamespace(id=match_id, result=result,
            stats={name: SimpleNamespace(grains=grains, clears=10, placed=100) for name in ('human', 'ai')},
            human=SimpleNamespace(step_count=100), ai=SimpleNamespace(step_count=100))

    def test_pagination_keeps_global_rank_and_out_of_page_profile(self):
        ids = [self.add_player(f'Player{i:02}') for i in range(25)]
        for i, user_id in enumerate(ids):
            self.store.record_match(self.match(str(i), 9000-i*100), user_id)
        first = self.store.standings(ids[22])
        second = self.store.standings(ids[22], 2)
        self.assertEqual(len(first['entries']), 20)
        self.assertEqual(len(second['entries']), 5)
        self.assertEqual(second['entries'][0]['rank'], 21)
        self.assertEqual(first['mine']['rank'], 23)
        self.assertEqual(len(first['top']), 10)
        self.assertEqual(self.store.standings(page=999)['page'], 2)
        self.assertEqual(self.store.standings(page=-1)['page'], 1)

    def test_wins_precede_grains_and_duplicate_results_are_ignored(self):
        alpha, bravo = self.add_player('Alpha'), self.add_player('Bravo')
        self.store.record_match(self.match('a1', 100), alpha)
        self.store.record_match(self.match('b1', 9000, 'AI wins'), bravo)
        self.store.record_match(self.match('b1', 9000, 'AI wins'), bravo)
        board = self.store.standings()
        self.assertEqual(board['top'][0]['username'], 'Alpha')
        self.assertEqual(board['matches'], 2)

    def test_legacy_matches_do_not_distort_detailed_efficiency(self):
        user = self.add_player('Alpha')
        self.store.record_match(self.match('new', 8000), user)
        with self.store.connect() as db:
            db.execute("INSERT INTO matches(match_id,user_id,result,human_grains,ai_grains,finished_at) VALUES('old',?,'Draw',500,500,0)", (user,))
        details = self.store.match_details(user)
        self.assertEqual(details['human_efficiency'], 80)
        self.assertEqual(details['human_average'], 4250)
        self.assertEqual(details['matches'], 2)
        self.assertEqual(details['detailed_matches'], 1)

    def test_migration_preserves_old_results(self):
        old_path = Path(self.directory.name) / 'old.sqlite3'
        with sqlite3.connect(old_path) as db:
            db.execute('CREATE TABLE matches(match_id TEXT PRIMARY KEY,user_id INTEGER,result TEXT,human_grains INTEGER,ai_grains INTEGER,finished_at INTEGER)')
            db.execute("INSERT INTO matches VALUES('legacy',1,'Draw',500,500,0)")
        migrated = AccountStore(old_path)
        with migrated.connect() as db:
            columns = {row[1] for row in db.execute('PRAGMA table_info(matches)')}
        self.assertTrue({'human_clears', 'human_placed', 'human_steps', 'ai_steps'} <= columns)
        self.assertEqual(migrated.global_stats()['human_grains'], 500)


if __name__ == '__main__':
    unittest.main()
