<h1 align="center">Sand Tetris Duel</h1>

<p align="center"><strong>A human vs AI sand game. Who clears more?</strong></p>

<p align="center">
  <a href="https://www.sandtrisduel.lol/"><strong>Play the game</strong></a> ·
  <a href="#the-website">The website</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#run-locally">Run locally</a>
</p>

<!-- MAIN DEMO: paste your GitHub-uploaded video URL here, or embed assets/readme/demo.gif. -->

<div align="center">

[![Languages](https://img.shields.io/badge/Languages-Python%203.12%20%7C%20C99%20%7C%20JavaScript-blue.svg)](#how-it-works)
[![Simulation](https://img.shields.io/badge/Simulation-C--Accelerated-brightgreen.svg)](#how-it-works)
[![Algorithm](https://img.shields.io/badge/Algorithm-CMA--ES%20%2B%20Color%20Lookahead-orange.svg)](#how-it-works)
[![Deployment](https://img.shields.io/badge/Deployment-Docker%20%2B%20Render-purple.svg)](#run-locally)

</div>

<img width="1270" height="830" alt="Ekran Resmi 2026-11-16 17 48 29" src="https://github.com/user-attachments/assets/349787e7-bde2-4707-af1f-b5cac4fceb59" />

## The website

I trained an AI to play the Sandtris. It is pretty decent from my test runs. It managed to survive 216,892 steps/pieces at one run, which is over 24 hours of gameplay, at about 0.25-0.3s per piece. The AI doesn't run that fast in the duel mode, instead it matches your speed for better experience. You can see in real time where the AI is placing the pieces, and the same seed helps since you are basically playing the same game. More technical details of the AI can be found here: <a href="https://github.com/ardasklrgl/SandtrisAI/"><strong>SandtrisAI</strong></a>

I built this so people could play against my Sandtris AI and see how they compare. 

Pieces break into sand, and a connected group of one color clears when it touches both walls. You and the AI get the same pieces based on a seed. The one who clears more sand grains with 100 pieces wins.

Signed in matches contribute to your record and the leaderboard when they finish. The leaderboard ranks players by wins minus losses, with grains cleared breaking ties.


### Practice

- Choose how many pieces to play.
- Switch between human and AI mode on the same board, without starting over.
- Let the AI play at its own pace, or pause to inspect the position.
- Toggle **AI hints** to see a heatmap along the pile. Stronger placements glow more brightly; weaker ones fade into the background. Hints are available during human play and while AI mode is paused, and are excluded from Duel.
- Track grains, clears, pile height, board averages and move timings in the stats panels.

<img width="1331" height="862" alt="Ekran Resmi 2026-11-16 17 54 58" src="https://github.com/user-attachments/assets/299db724-da6b-4a99-84c2-4ad7e96d2485" />


### Accounts and leaderboard

- Completed signed-in duels contribute to your record and the global standings.
- Players are ranked by wins minus losses, with total grains cleared breaking ties.
- Guest games also have a separate record in the current browser.
- Includes detailed stats for AI vs Humans

<img width="1249" height="742" alt="Ekran Resmi 2026-11-16 17 55 23" src="https://github.com/user-attachments/assets/00adebc8-1c30-469f-9904-f79894feed2a" />

<img width="1358" height="548" alt="Ekran Resmi 2026-11-16 18 04 40" src="https://github.com/user-attachments/assets/d11033b3-5807-4816-9a4f-73d86a121423" />

### Interface and controls

The site has a frosted frame, black game boards and an animated text background. The two interface accent colors shift continuously; the sand colors stay fixed.

**Controls:** arrows or WASD to move/rotate, Space to drop or resume, P to pause. There are on-screen controls too.

## How it works

The website splits the work between the browser, a **Python server**, and a **C simulation core**. JavaScript handles your controls and draws the boards with Canvas, while WebGL renders the animated text background. When you drop a piece, the browser sends its placement to the server. The server runs the physics, updates the score, and returns the resulting board and sand-animation frames for the browser to play back.

The board is an **85 × 150 grain grid**, and each piece breaks into 100 grains. After a placement, the sand settles and the game checks for connected groups of the same color touching both walls. Those grains are removed, then the remaining sand settles again, which can lead to another clear. Both duel boards use the same physics and receive the same seeded sequence of pieces.

The AI scores possible placements using **24 board features**, including pile height, bumpiness, color connectivity and gaps. These features are normalized and clipped, then combined with a learned weight vector using NumPy. I optimized the weights offline with **CMA-ES**, which evaluates different weight vectors over games and adapts its search toward better-performing ones. During gameplay the weights stay fixed: inference consists of simulating and scoring moves. The training side of the project is in [Sandtris AI](https://github.com/ardasklrgl/SantrisAI).

For each move, the bot evaluates up to **68 placements**: 17 horizontal positions across four rotations. It takes the best three into a second search step. Since the next piece's color matters a lot, the lookahead samples one shape for each of the four possible colors and uses the same samples for every candidate. It combines the immediate score with half the average best future score. This lets it consider what a placement sets up, alongside what it clears immediately. The expensive sand simulations and spatial feature evaluation run in C; Python coordinates the search.

To keep Duel responsive, random games cycle through **20 seeds with precomputed AI actions**. For custom seeds, the server prepares up to six moves ahead while you play. Practice evaluates moves live, so the AI can take over a board you've already built. Calculation speed depends on the position and server load, and the stats panels show move timings as you play.

The hint heatmap uses the same trained evaluator, averaging placement scores across valid rotations before lookahead. It blends stronger choices into brighter regions along the pile, with weaker choices fading away. It therefore explains the evaluator's preferences without necessarily predicting the full search's final choice. Hints are restricted to Practice, and AI mode only displays them while paused.

Accounts and completed signed-in results are stored in **SQLite**, while active games stay in server memory. The server determines the final result before adding it to the leaderboard. The app is packaged with **Docker** and deployed on **Render**.

### Repository layout

```text
app/             Python server, gameplay, physics bindings and AI
native/          C simulation source and compiled library
models/          Trained weights and precomputed AI plans
web/             Browser JavaScript, CSS and game rendering
scripts/         Offline utilities, including AI plan generation
examples/        Earlier standalone interface demos
tests/           Gameplay, AI, account and ranking checks
assets/readme/   README media
design/          Background assets and design explorations
```

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
cc -O3 -std=c99 -shared -fPIC native/sandtris_c_core.c -o native/sandtris_c_core.so
python -m app.web_flow
```

Open [localhost:8770](http://localhost:8770). Set `SANDTRIS_DB_PATH` to choose where account data is stored; the default is `/tmp/sandtris-duel-accounts.sqlite3`.

With this Python setup, run the tests using:

```sh
python -m unittest discover -s tests
```

</details>
