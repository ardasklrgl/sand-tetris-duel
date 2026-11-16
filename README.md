<h1 align="center">Sand Tetris Duel</h1>

<p align="center"><strong>A human vs AI sand game. Same pieces. Who clears more?</strong></p>

<p align="center">
  <a href="https://www.sandtrisduel.lol/"><strong>Play the game</strong></a> ·
  <a href="#the-website">The website</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#run-locally">Run locally</a>
</p>

<!-- MAIN DEMO: paste your GitHub-uploaded video URL here, or embed assets/readme/demo.gif. -->

<p align="center">
  <code>Python</code> <code>C</code> <code>JavaScript</code>
  <code>Canvas / WebGL</code> <code>SQLite</code> <code>Docker</code> <code>Render</code>
</p>

## The website

I built this so people could play against my Sandtris AI and see how they compare. Pieces break into sand, and a connected group of one color clears when it touches both walls.

### Duel

You and the AI receive the same sequence of shapes and colors. After 100 pieces, whoever cleared more grains wins. You can replay a seed or share it with someone else to try the same game.

<!-- Optional Duel clip: assets/readme/duel.gif -->

### Practice

- Choose how many pieces to play.
- Switch between human and AI mode on the same board, without starting over.
- Let the AI play at its own pace, or pause to inspect the position.
- Toggle **AI hints** to see a heatmap along the pile. Stronger placements glow more brightly; weaker ones fade into the background. Hints are available during human play and while AI mode is paused, and are excluded from Duel.
- Track grains, clears, pile height, board averages and move timings in the stats panels.

<!-- Optional Practice / hints clip: assets/readme/practice.gif -->

### Accounts and leaderboard

Completed signed-in duels contribute to your record and the global standings. Players are ranked by wins minus losses, with total grains cleared breaking ties. Guest games also have a separate record in the current browser.

### Interface and controls

The site has a frosted frame, black game boards and an animated text background. The two interface accent colors shift continuously; the sand colors stay fixed.

**Controls:** arrows or WASD to move/rotate, Space to drop or resume, P to pause. There are on-screen controls too.

## How it works

| Part | What it does |
| --- | --- |
| **JavaScript, HTML and CSS** | Controls, pages, animation playback and UI. Canvas draws the game; WebGL renders the text background. |
| **Python** | Game sessions, turn handling, AI search and HTTP endpoints. |
| **C** | Sand simulation and candidate-placement evaluation. |
| **NumPy** | Feature vectors and weighted AI scoring. |
| **SQLite** | Accounts, sessions and completed signed-in results. |
| **Docker / Render** | Builds and hosts the deployed game. |

### AI and inference

The AI uses a trained weighted evaluator with two-step color lookahead. It scores up to **68 placements** (17 columns × 4 rotations) using **24 clipped board features**, then runs lookahead on the best three.

For lookahead, it samples one shape for each possible next color. It uses the same samples to compare candidates, combining the current placement score with their average best future score.

Inference and authoritative sand physics run on the server. The browser sends moves and renders the returned board states and animation frames.

### Keeping moves responsive

Duel cycles through **20 precomputed seeds**, so those AI actions are already available. For custom seeds, the server prepares up to six moves ahead while you play. Practice calculates AI moves live so it can take over a board built by a human. Move times depend on the position and server load.

The hint heatmap averages evaluator scores across valid rotations, **before lookahead**. It shows what the evaluator prefers, so it won't always match the full search's final choice.

## Run locally

### Docker

Install Docker, then:

```sh
git clone https://github.com/ardasklrgl/sand-tetris-duel.git
cd sand-tetris-duel
docker build -t sand-tetris-duel .
docker run --rm -p 10000:10000 -v sandtris-duel-data:/app/data sand-tetris-duel
```

Open [localhost:10000](http://localhost:10000). The named volume keeps accounts and standings in SQLite. Active games live in memory and reset when the server restarts.

<details>
<summary>Run directly with Python instead</summary>

Use Python 3.12 and a C compiler on Linux or macOS:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-web.txt
cc -O3 -std=c99 -shared -fPIC sandtris_c_core.c -o sandtris_c_core.so
python web_flow.py
```

Open [localhost:8770](http://localhost:8770). Set `SANDTRIS_DB_PATH` to choose where account data is stored; the default is `/tmp/sandtris-duel-accounts.sqlite3`.

With this Python setup, run the tests using:

```sh
python -m unittest discover -s tests
```

</details>
