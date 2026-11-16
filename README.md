# Sand Tetris Duel

I built this so people could play against my Sandtris AI and see how they compare. It's Tetris with sand: pieces break into grains, and connecting one color from wall to wall clears it.

**[Play here → sandtrisduel.lol](https://www.sandtrisduel.lol/)**

## Features

- **Duel:** you and the AI get the same seeded pieces. Clear more grains over 100 pieces to win.
- **Practice:** choose the piece count, play yourself or let the AI take over. Switching modes keeps the same board.
- **AI hints:** a heatmap along the pile shows which placements the evaluator prefers. Practice only; pause AI mode to inspect it.
- **Detailed stats:** grains, clears, pile height, board averages and move timings.
- **Replayable seeds:** replay a game or share its seed with someone else.
- **Accounts and leaderboard:** completed signed-in duels count toward your record and the global standings.
- Frosted UI, an animated text background and a continuously changing two-tone palette.

## The AI / inference

The AI uses a trained weighted evaluator with two-step color lookahead. It scores up to **68 placements** (17 columns × 4 rotations) using **24 clipped board features**, then runs lookahead on the best three. It samples one shape for each possible next color and uses the same samples to compare candidates by their average best future score.

Python handles the search and game server. C handles the sand simulation and feature evaluation. The browser handles controls, rendering and animation; inference runs on the server.

Duel cycles through **20 precomputed seeds** to avoid waiting for AI decisions. Custom seeds are evaluated live, with up to six moves prepared ahead. Practice AI calculates moves live so it can take over any human-built board. Its speed depends on the server and current position.

The hint heatmap combines placement scores across valid rotations, before lookahead. It's a way to inspect the evaluator, so it won't always predict the full search's choice.

## Run locally

```sh
docker build -t sand-tetris-duel .
docker run --rm -p 10000:10000 -v sandtris-duel-data:/app/data sand-tetris-duel
```

Open [localhost:10000](http://localhost:10000). The volume keeps accounts and leaderboard data in SQLite. Active games are held in memory and reset when the server restarts.

**Controls:** arrows or WASD to move/rotate, Space to drop or resume, P to pause.

Run tests with `python -m unittest discover -s tests`.
