# Sand Tetris Duel

A 100-piece Sand Tetris duel: you and the color-lookahead AI receive the same seeded pieces. The Python server handles sand physics, AI moves, accounts, and completed-match standings.

## Run locally

With Docker installed:

```sh
docker build -t sand-tetris-duel .
docker run --rm -p 10000:10000 -v sandtris-duel-data:/app/data sand-tetris-duel
```

Open http://127.0.0.1:10000. The health check is at `/health`.

Without Docker, install `requirements-web.txt`, compile `sandtris_c_core.c` into `sandtris_c_core.so` for your platform, and run `python web_flow.py`. The local default URL is http://127.0.0.1:8770. Set `SANDTRIS_DB_PATH` to choose where the SQLite account and leaderboard data lives; the local preview defaults to `/tmp/sandtris-duel-accounts.sqlite3`.

## Publish a playtest

Push this repository to GitHub. In Render, create a **Web Service** from it with **Language: Docker** and **Health Check Path: /health**. The Dockerfile starts the duel server on the host-provided port.

The leaderboard counts completed matches started while signed in. It ranks players by wins minus losses, then total grains cleared. The game page's global AI-versus-human figures use those same completed matches; its separate browser-only record also includes guest games. Account and ranked match data is stored in SQLite; configure a persistent disk mounted at `/app/data` for a hosted service. In-progress matches remain in server memory and disappear on restart; the server handles up to 16 active matches. Use this version for a small playtest rather than a large public launch.

The game page previews the top 10 players. The leaderboard page includes a personal profile, AI/human comparisons, and standings paginated at 20 players. New matches record clears, placement counts, and pieces played; historical matches without those fields continue to count toward wins and grains. Run the account and ranking checks with `python -m unittest discover -s tests -v`.
