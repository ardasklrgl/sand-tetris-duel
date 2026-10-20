"""Generate deterministic AI action plans for the 100-piece web duel."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import random

import numpy as np

from web_game import calculate_ai_action, load_weights, plan_fingerprint
from web_physics import LiveEnv


def plan_seed(seed):
    env = LiveEnv()
    env.reset(seed=seed)
    rng = np.random.default_rng(np.random.SeedSequence([seed, 731]))
    weights = load_weights()
    actions = []
    for _ in range(100):
        action = calculate_ai_action(env, weights, rng)
        actions.append(action)
        _, _, done, _, _ = env.step(action)
        if done:
            break
    return seed, actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--output", type=Path, default=Path("precomputed_ai.json"))
    args = parser.parse_args()
    if not 1 <= args.count <= 1000 or args.workers < 1:
        parser.error("count must be 1–1000 and workers must be positive")

    generator = random.Random(20261020)
    seeds = set()
    while len(seeds) < args.count:
        seeds.add(generator.getrandbits(32))
    plans = {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(plan_seed, seed): seed for seed in sorted(seeds)}
        for future in as_completed(futures):
            seed, actions = future.result()
            plans[str(seed)] = actions
            print(f"{len(plans)}/{len(seeds)} seeds: {seed}, {len(actions)} moves", flush=True)

    args.output.write_text(json.dumps({
        "fingerprint": plan_fingerprint(),
        "seeds": dict(sorted(plans.items(), key=lambda item: int(item[0]))),
    }, separators=(",", ":")) + "\n")
    print(f"Wrote {args.output}", flush=True)


if __name__ == "__main__":
    main()
