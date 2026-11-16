# AI assets

- `best_clipped_weights_run2.npy`: the trained 24-feature evaluator weights.
- `precomputed_ai.json`: action plans for the 20 bundled Duel seeds.

The plans include a source fingerprint. Changes to the policy, physics or weights
disable stale plans automatically. Regenerate them from the repository root with:

```sh
python -m scripts.precompute_ai --count 20 --workers 4
```
