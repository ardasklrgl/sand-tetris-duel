# Sand Tetris Duel — publishing and browser-engine handoff

Prepared: 19 October 2026  
Status: implementation plan; browser migration and public deployment are not complete.

## 1. Objective

Publish the existing Sand Tetris Duel website while moving gameplay physics and AI calculation into each player's browser. Preserve the current visual design, human controls, sand behavior, two-step color lookahead AI, and 100-piece match format.

Keep a small backend for accounts, persistent statistics, ranked-match validation, and leaderboards. Avoid doing AI search on the server for every turn of every casual match.

The first implementation milestone is **one complete 100-piece duel running in the browser, in the current interface, with behavior checked against the Python reference**. Hosting comes after that milestone.

## 2. Repository and current state

Current local repository:

```text
/Users/ardasiklaroglu/sand-tetris-duel
https://github.com/ardasklrgl/sand-tetris-duel
```

The repository was previously under `/Users/ardasiklaroglu/projeler/sand-tetris-duel`. Check the actual checkout rather than relying on that old path.

At the time of this handoff, important work is modified or untracked locally. In particular, the flow design, account code, background assets, and tests may not yet exist in the remote repository. Inspect `git status` and preserve these files before any checkout, reset, cleanup, or deployment. A clone of the remote alone may be incomplete.

### Current file map

| File | Responsibility |
| --- | --- |
| `web_flow.py` | Current website: game page, About, login/account, detailed leaderboard, shared visual styles, routes. This is the design to publish. |
| `web_demo.py` | 100-piece match subclass and demo client behavior reused by the flow page. |
| `web/app.js` | Human input, falling piece, canvas drawing, animation playback, and current game API client. |
| `web_game.py` | Server match lifecycle, AI preparation, statistics, turn execution, and base HTTP handling. |
| `web_physics.py` | `LiveEnv`: local C sand simulation, repeated settling after clears, and captured animation frames. |
| `sandtris_env_v10.py` | Board, piece definitions, environment, native integration, and random piece generation. |
| `sandtris_lookahead_bot.py` | Two-step color lookahead search orchestration. |
| `sandtris_parameterized_bot.py` | Feature extraction, normalization, and native evaluator bindings. |
| `sandtris_c_core.c` | Native simulation/evaluation routines; contains shared scratch buffers. |
| `best_clipped_weights_run2.npy` | Current trained evaluator weights. |
| `web_accounts.py` | SQLite users/sessions/results, ranking, pagination, and aggregated statistics. |
| `web/account.js` | Login/signup modes, username availability, and form feedback. |
| `web/beach-background.js` | Animated video-to-text beach background and shifting palette. |
| `design/beach/assets/` | Bundled video, poster, and text used by the background. |
| `tests/test_web_accounts.py` | Existing account-store migration and ranking checks. |
| `Dockerfile`, `.dockerignore` | Current server deployment build and included files. |

### What runs where today

- The browser handles input, rendering, and playback of sand animation frames.
- Python executes both boards' authoritative placements, sand physics, and AI search.
- `/api/new`, `/api/state`, and `/api/move` drive the current server-hosted match.
- AI and native work are serialized through `ENGINE_LOCK`; `THINKER` has one worker. The native C evaluator uses shared scratch buffers.
- The current service retains up to 16 active matches in memory. In-progress games disappear on restart.
- Accounts and completed signed-in results are stored in SQLite.
- Local database default: `/tmp/sandtris-duel-accounts.sqlite3`. This is a preview default, not a durable production storage choice.
- Docker database default: `/app/data/accounts.sqlite3`, configured with `SANDTRIS_DB_PATH`.
- The Docker entry point already starts `web_flow.py`, not an older visual demo.

Local reference commands, after dependencies/native compilation are available:

```sh
python web_flow.py --port 8770
python -m unittest discover -s tests -v
```

## 3. Requirements to preserve

### Gameplay and AI

- Board size: 85 × 150 grains.
- Both sides receive the same sequence of shapes and colors from the same match seed.
- Each tetromino consists of 5 × 5 grain blocks; a complete piece contributes 100 grains.
- Human movement is grain-level, not restricted to bot placement columns.
- Preserve Arrow keys/WASD, rotation, soft drop, Space/drop, pause, and current button behavior.
- Preserve the current interaction between visual settling and the next playable piece. Do not introduce a requirement to wait for every animation frame before accepting play.
- The AI prepares ahead while the human plays; pause for it only if its next move is genuinely unfinished.
- AI configuration: two-step lookahead, `lookahead_mode="color"`, `k=3`, clipped feature extraction, and the existing weights. Do not silently weaken search depth to improve benchmarks.
- Preserve scoring definitions, clear timing, rotation conventions, top-out handling, and match-end rules from the current runtime. At the 100-piece limit, compare grains cleared. Check the existing early top-out behavior separately; do not replace it accidentally.
- Orthogonal connectivity determines a clearing component. A same-color connected component must touch both side walls; diagonal contact alone does not connect grains.

### Visual and product design

Retain the current flow design: dark translucent outer frame, black cards, wide dark shadows, monospace typography, small white section headings, rounded controls, and slowly changing opposing accent colors.

- Game sand colors stay fixed. Only the interface/background palette changes.
- Palette phase persists across page navigation.
- Navigation remains one row: About | Leaderboard | Background | Account.
- Account status square is gray when signed out and lit when signed in.
- Background view leaves only Return visible.
- Title animation runs on the initial open or title click, not every navigation.
- AI is left and humans/you are right in score panels and bars.
- Preserve the current accent drop/login buttons, black outlined controls, and compact login form.
- Main page ends with a top-10 leaderboard preview. Full leaderboard has 20 entries per page and a separate own row when needed.
- Rank by wins minus losses, then total grains cleared, then a stable final tie-breaker. Preserve the current rank-color transition and top-three number/name glow. No medal shapes or profile achievement badges for now.
- Keep About text and social links. X: `https://x.com/cupsyx`; GitHub: `https://github.com/ardasklrgl`; email: `mailto:ardasklrgl@gmail.com`.
- Cursor proximity amplifies the background's existing colored light; do not add a white/radial overlay.

Current background settings: letter size 4 px, brightness 1.2, threshold 0.42, glow 1.5, video playback 0.55×. Preserve the bundled loop treatment. A quality reduction for slow devices may be added without changing game rules.

Do not redesign the website or introduce a new UI framework solely for this migration.

## 4. Target architecture

```text
Browser
  Existing UI, input, canvases, background, local match controller
       │ messages / transferable buffers
       ▼
  Web Worker
    Deterministic live physics + C evaluator compiled to WebAssembly
    Two-step color lookahead + trained weights + separate RNG states

Backend
  Accounts/sessions, ranked match issuance, result submission,
  verification jobs, persistent statistics, leaderboard
       │
       ▼
  Persistent SQLite + backups initially
```

A player does not need to install Python or download an executable. Browser workers execute the game engine off the UI thread. WASM compilation does not itself port the Python orchestration or SciPy clearing logic; those need explicit implementation.

Prefer one same-origin `/api/` surface for the browser. If static hosting and the Python service use different origins, choose and document either a same-origin proxy or a narrowly configured cross-origin cookie/CORS arrangement. Do not leave session-cookie behavior to chance.

Keep the existing Python backend initially. Moving accounts to another platform is a separate decision and is not required to move gameplay off the server.

## 5. Critical compatibility work

### Live physics uses the trained sand simulation

`LiveEnv.settle()` uses the local C sand simulation and clears wall-to-wall components after settling. It repeats the sand simulation after each clear until the remaining grains rest. The AI evaluator uses the same C sand step, while its feature scorer still evaluates one drop at a time. Captured frames sample every native tick before downsampling for browser playback. Preserve the post-clear settling rule when porting the game.

Port four-neighbor component labeling/clearing explicitly; SciPy does not become a browser dependency automatically. Preserve component removal order where it affects subsequent states.

### Randomness, ties, and replay versioning

Inventory both random streams: NumPy's piece sequence and the independent lookahead shape-sampling stream derived from `[seed, 731]`. Cloning must copy their state correctly.
Feature extraction must not draw from the match's piece sequence; precomputed AI plans must replay against the same pieces the player sees.

Choose a compatibility strategy after a small spike:

1. Reproduce the existing generators and draw order exactly, or
2. Deliver deterministic piece/search schedules where feasible while preserving the native sand simulation, or
3. Introduce a versioned portable RNG only with explicit approval of changed seed behavior and regression evidence.

Do not claim old-seed compatibility if the sequence changes. Record engine, RNG, evaluator/weights, and rules versions with ranked matches. Define deterministic candidate tie-breaking; NumPy sorting and floating-point differences can otherwise change AI choices.

### Worker ownership and native state

Use a single engine worker initially. Keep live boards, simulation clones, and native scratch state owned by it. Do not concurrently call a WASM evaluator instance whose scratch buffers are shared. Avoid transferring the only authoritative board buffer out of the worker; transfer snapshots or a controlled buffer pool.

Use cancellable/versioned work: restarting a match must make stale AI replies harmless. Backgrounding, pausing, resize, and slow AI responses must not advance a turn twice.

## 6. Implementation phases and acceptance gates

### Phase A — preserve and measure the reference

Tasks:

- Inspect local instructions and working-tree changes; save all needed source/assets without discarding local edits.
- Capture representative screenshots and record the exact rules, runtime versions, weights hash, and RNG behavior.
- Create replay fixtures covering normal play, multiple clears, diagonal-only contact, blocked placements, top-outs, and the 100th turn.
- Record boards and RNG state at useful checkpoints, with authoritative scores and AI choices.
- Measure native AI and physics separately from frame encoding/network transfer and background rendering.

Deliverables: reference fixtures, a behavior specification, screenshots, and a baseline benchmark report.

Gate: the current build is reproducible and its expected behavior is recorded before engine replacement.

### Phase B — deterministic browser-engine spike

Tasks:

- Add a pinned Emscripten build for the C evaluator and a small worker entry point.
- Port live placement, settling, clearing, scoring, and RNG/cloning behavior.
- Port feature normalization and color lookahead orchestration; export weights in a browser-readable format with a version/hash.
- Expose a small engine interface: initialize/reset, validate/apply human input or placement, prepare AI, snapshot, replay, and cancel/dispose.
- Keep search calculation separate from animation playback speed.

Deliverables: reproducible `.wasm` build, worker, engine adapter, fixture runner, and documented compatibility decisions.

Gate: one complete local browser duel matches the reference, or any unresolved differences are reported precisely. Do not proceed as if different physics were equivalent.

### Phase C — connect the current UI

Tasks:

- Extract the necessary static page assets from `web_flow.py` while preserving layout. No framework rewrite is required.
- Replace turn-by-turn game HTTP calls with worker messages. Keep account/statistics calls online.
- Prepare the AI ahead, retain current paired-turn behavior, and avoid blocking controls with WASM work.
- Include turn/match generation IDs and structured worker errors.
- Bound animation buffers and release old match resources.
- Add concise engine-loading/error states. Guest play should work after assets load even if the account API becomes unavailable.

Gate: the full UI runs a 100-piece duel without `/api/move` or per-turn physics/AI requests. Restart, pause, seed replay, navigation, and final results behave correctly.

### Phase D — parity and device performance

Tasks:

- Run the reference fixtures against native and WASM builds. Compare board cells, piece sequences, RNG states where available, scores, and AI actions.
- Separate intentional engine-version changes from implementation bugs.
- Test Chrome, Firefox, Safari, Android Chrome, and iOS Safari on real devices where available. Emulation alone is not a phone-performance test.
- Measure input responsiveness, AI median/p95 preparation time, physics time, memory, long-frame frequency, and background cost.
- Check slow devices, hidden tabs, rapid input, interrupted loading, and repeated restarts.

Provisional performance targets: responsive controls with no main-thread engine stalls; AI p95 preparation under 1 second on an ordinary laptop and under 2 seconds on a representative phone. These are targets to validate, not measured promises. Optimize implementation/background quality before proposing a weaker bot.

Gate: publish measurements and remaining device limitations. Rendering or OS/browser issues must not silently change game rules or the piece sequence.

### Phase E — trusted ranked matches

Recommended initial design: a server-managed pool of ranked seeds with AI trajectories precomputed once per engine version. Browser AI still runs locally for ordinary gameplay; ranked AI moves must match the trusted trajectory. The backend replays the human's legal moves, computes its score, and compares it with the trusted AI result.

Precomputation amortizes AI search across players sharing a seed. It does not remove human replay verification cost, and a small/reused seed pool can become learnable. Measure cost and choose a sufficiently broad pool/rotation policy before launch.

Tasks:

- Build and store AI trajectories with seed, versions, weights hash, legal actions, board checkpoints, scores, and top-out state.
- Issue an authenticated ranked match ID bound to the user, seed, and version. Casual matches can remain local.
- Record a bounded, ordered replay. Validate legal human movement, not just in-bounds final coordinates: an arbitrary `{x,y,rotation}` must not permit teleporting pieces into unreachable spaces.
- Choose either deterministic tick/input replay or formally validated reachable placements that preserve the current control rules. Document pause/soft-drop/animation semantics.
- Accept submissions idempotently and verify in a background job. Treat browser-reported scores, AI results, and board hashes as untrusted.
- Use native live physics matching the browser version to calculate the authoritative human score. Check the AI trajectory/version and terminal conditions.
- Show pending results until verification succeeds; update public aggregates exactly once after verification.
- If precomputation proves impractical, benchmark full asynchronous native AI replay instead and revise compute estimates before deployment.

Gate: forged scores, illegal placements, replay truncation, wrong versions, duplicate submissions, and unauthorized match IDs cannot create leaderboard results. Verification does not hold open a normal web request for an entire game.

### Phase F — accounts and persistent data

Tasks:

- Retain the current username/password flow and accessibility. Preserve case-insensitive username uniqueness.
- Run the HTTP API with a production-capable server/framework; the current standard-library preview handler is not the final production server.
- Preserve password hashing and opaque sessions; use secure HTTP-only cookies over HTTPS, appropriate SameSite/CSRF protection, and strict origin handling.
- Bound login/signup/submission requests and replay sizes. Make rate limiting meaningful behind the hosting proxy rather than accidentally limiting everyone as one proxy IP.
- Migrate the existing database additively. Do not erase accounts/results or mix incompatible engine versions.
- Add persistent ranked-match and verification-job state. In-memory jobs alone are insufficient across deploys.
- Separate local test results, pending results, rejected results, and verified public results. Only verified results feed the public scoreboard/leaderboard.
- Retain existing account tests; add focused migration, verification, authorization, and idempotency tests.

Suggested additional entities: `engine_versions`, `ranked_seeds`, `ai_trajectories`, `ranked_matches`, `verification_jobs`, and replay storage. Existing `users`, `sessions`, and completed-result tables can be retained/migrated.

Gate: accounts and verified records survive restart/redeploy; failed/retried jobs cannot double-count results; previous data has a documented migration path.

### Phase G — staging deployment

Tasks:

- Build static assets and WASM reproducibly in CI; build the native verifier separately. Update Docker/context inclusion for every required file.
- Deploy the frontend to Cloudflare static hosting and the backend to a small paid Render service, initially using persistent SQLite.
- Prefer same-origin API routing. Never cache authentication or personalized API responses at the CDN.
- Mount durable storage at `/app/data` and set `SANDTRIS_DB_PATH=/app/data/accounts.sqlite3`. A Docker `ENV` value alone does not create durable hosting storage.
- Keep one SQLite-owning backend instance initially. Additive migrations run in a controlled startup/deployment step. Move to a shared database before attempting multi-instance scaling.
- Configure HTTPS, production origin, secret storage, health checks, logging, and database backups.
- Back up SQLite through its backup API or another consistent backup method, not an arbitrary copy of a live file. Perform an actual restore test.
- Confirm WAV/MP4/WASM MIME types as applicable, asset caching/versioning, video loading, and source-asset publication rights.
- Keep the current background fallback and reduced-motion behavior. Avoid exposing database files, secrets, test fixtures, or personal logs as static assets.

Gate: complete signup → local play → submission → verification → leaderboard on staging, then restart/redeploy and confirm persistence. Test service failure and recovery as well as the happy path.

### Phase H — limited playtest, then launch

- Start with a small invited group and inspect verified-match completion, queue delay, rejection reasons, slow-device reports, and resource use.
- Tune only where measurements justify changes. Preserve screenshots/design and avoid a last-minute UI rebuild.
- Add a short privacy notice describing account/session/match data and an account deletion/contact route. Do not log passwords or session tokens.
- Configure the chosen domain, HTTPS redirects, monitoring, and spending alerts. Confirm billing settings and how to disable expensive jobs.
- Publish once the launch checklist below passes. Deploying to public services or purchasing a domain is a separate external action; this document itself authorizes no purchase or publication.

## 7. Proposed API and state transitions

These are proposed interfaces, not routes already implemented:

| Endpoint | Purpose |
| --- | --- |
| `POST /api/ranked-matches` | Issue a user-bound match ID, seed, versions, and trusted AI reference. |
| `POST /api/ranked-matches/{id}/submit` | Store bounded replay; return pending status; repeat submissions are idempotent. |
| `GET /api/ranked-matches/{id}` | Return authorized match/verification status and final authoritative result. |
| `GET /api/profile` | Current user's verified statistics and rank. |
| `GET /api/leaderboard?page=1` | 20 verified ranked players plus pagination metadata. |
| `GET /api/leaderboard/top` | Lightweight top-10 preview. |
| `GET /api/stats` | Public AI-versus-human totals. |

Keep/adapt current login, signup, logout, and username availability endpoints. Use structured validation errors without leaking credentials/internal traces.

Suggested lifecycle:

```text
issued → submitted → verifying → verified
                             └→ rejected
issued → expired / forfeited (policy decision below)
```

Persist transitions and retries. A verified match is immutable for ordinary clients. Use bounded backoff/status polling; no per-frame or per-turn network polling.

## 8. Decisions to resolve before public ranked launch

These have been suggested, but should not be silently treated as approved product rules:

| Decision | Starting recommendation |
| --- | --- |
| Repeated ranked seeds | Unlimited practice; only the first ranked attempt per account/seed/version counts. |
| Abandoning/restarting a ranked game | Define an explicit forfeit/expiry policy. Currently abandoned games do not count as losses. Avoid a leaderboard that can be inflated by discarding every losing attempt. |
| Disconnects/resume | Allow a bounded resume window; replay and trusted server state must prevent attempt substitution. |
| Existing playtest accounts/results | Preserve accounts; keep unverified historical results separate from the new public ranked competition. |
| Engine updates | Pin issued matches to their version; document whether the leaderboard resets by season/version or remains comparable. |
| Ranked seed visibility | Assume browser code/seeds/AI moves can be inspected. Precomputed seeds reduce verification cost, but do not prevent practice or automated assistance. |
| Old seed compatibility | Preserve exact behavior where feasible; require an explicit version change if RNG/physics must change. |
| Domain and budget | Owner chooses final domain and approves paid-service setup before spending. |

Replay validation verifies consistency with game rules, not that a human personally supplied the inputs. A browser game cannot guarantee absence of automation. Do not market the leaderboard as cheat-proof.

## 9. Cost model and initial allowance

Planning allowance: **US$10–20/month for a small initial launch**, plus roughly **US$10–20/year reserved for a domain**. The domain figure is a budget allowance, not a registrar quotation. Taxes, exchange rates, bandwidth overages, and heavier verification can increase cost.

Pricing snapshot researched on 19 October 2026; recheck before purchasing:

| Component | Starting assumption |
| --- | --- |
| Cloudflare static assets | Free static-asset requests; backend/proxy function usage has separate quotas. |
| Small paid Render service | US$7/month, 0.5 CPU / 512 MB listed tier. Capacity must be benchmarked with the verifier. |
| Render persistent disk | US$0.25/GB/month; 1 GB gives an illustrative US$7.25 server+disk base. |
| Optional future Cloudflare backend rewrite | Workers paid starts at US$5/month, but this is an alternative architecture, not an extra requirement or a direct home for the existing Python/native backend. |

The bot has no paid model/API inference fee. Main costs are serving assets, account/database traffic, AI seed precomputation, and replay verification.

Estimate compute from measurements:

```text
AI precomputation ≈ new ranked seeds × up to 100 turns × measured AI time/turn
Human verification ≈ completed ranked matches × turns/match × measured replay physics time/turn
```

Also budget for retained replay storage, backups, and asset/video bandwidth. Keep assets on static hosting/CDN rather than repeatedly serving them through the Python API. Do not promise that US$7.25 will support an unspecified number of simultaneous players or ranked games. Measure queue drain rate and memory before choosing the paid instance.

## 10. Launch checklist

- [ ] Local source, untracked files, weights, and background assets are preserved and included in the deployable repository.
- [ ] Current design is retained on desktop/mobile; screenshots reviewed.
- [ ] A full browser duel works without per-turn server simulation requests.
- [ ] Seeds, physics, clearing, scores, RNG/cloning, and AI behavior pass recorded compatibility checks.
- [ ] Browser/device measurements are recorded; slow/failing-engine behavior is understandable.
- [ ] Ranked rules and legacy-data treatment are explicit.
- [ ] Human replays and trusted AI references are verified server-side; client scores alone never update public rankings.
- [ ] Verification is persistent, bounded, retryable, and idempotent.
- [ ] Login, session handling, authorization, origin checks, and request limits work over production HTTPS.
- [ ] Accounts/results survive a redeploy; a backup has been restored successfully.
- [ ] Static assets/WASM/video load correctly; no secrets/databases/test fixtures are publicly served.
- [ ] Health checks, monitoring, queue/resource metrics, and spending alerts are configured.
- [ ] Privacy/contact information is present and asset publication rights are checked.
- [ ] An invited playtest completes the entire ranked flow successfully.
- [ ] Owner has approved domain/hosting spend and public deployment.

## 11. Rollback and agent reporting

Keep versioned engine assets and the native verifier for issued matches. Prefer additive schema changes so the previous release can still read its data. If verification fails, pause new ranked issuance and keep local/casual play available; do not publish unchecked results to make the queue disappear.

Do not roll the public service back to per-turn server AI at full traffic without re-evaluating capacity. Keep the old server engine as a reference/test implementation and controlled fallback for development.

At each phase, the implementing agent should report:

1. Files and behavior changed.
2. Evidence from parity tests, browser/device checks, and measurements.
3. Any RNG/physics/ranked-policy decisions still requiring owner input.
4. Exact staging/production configuration and costs introduced.
5. Remaining work and rollback instructions.

Start with Phase A and the deterministic-engine spike. Avoid an all-at-once frontend/backend/hosting rewrite. Do not begin with deployment and assume browser-engine parity can be solved afterward.

## 12. References

- Emscripten: https://emscripten.org/docs/introducing_emscripten/about_emscripten.html
- Cloudflare static-asset billing: https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/
- Cloudflare Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
- Render pricing: https://render.com/pricing
- Render persistent disks: https://render.com/docs/disks

Provider limits/prices are changeable. Reference URLs and this plan are starting points; verify the actual account's settings and current terms before enabling billing or launching.
