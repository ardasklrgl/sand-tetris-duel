# Sand Tetris Duel

A 100-piece Sand Tetris duel: you and the color-lookahead AI receive the same seeded pieces. The game runs in a browser, with a Python server handling sand physics and AI moves.

## Run locally

With Docker installed:

```sh
docker build -t sand-tetris-duel .
docker run --rm -p 10000:10000 sand-tetris-duel
```

Open http://127.0.0.1:10000. The health check is at `/health`.

Without Docker, install `requirements-web.txt`, compile `sandtris_c_core.c` into `sandtris_c_core.so` for your platform, and run `python web_demo.py`. The local default URL is http://127.0.0.1:8766.

## Publish a playtest

Push this repository to GitHub. In Render, create a **Web Service** from it with **Language: Docker** and **Health Check Path: /health**. The Dockerfile starts the duel server on the host-provided port.

The global scoreboard currently shows illustrative figures, not live results. The personal win/loss record is stored in each browser. In-progress matches are held in server memory and disappear on restart; the server handles up to 16 active matches. Use this version for a small playtest rather than a large public launch.
