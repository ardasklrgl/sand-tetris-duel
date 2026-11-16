"""Read-only placement evaluation for the Practice hint overlay."""
import numpy as np
from sandtris_parameterized_bot import extract_features
from web_game import ENGINE_LOCK


def placement_hints(match, turn, rotation):
    with match.lock:
        if turn != match.turn:
            raise ValueError('The board has advanced.')
        if match.result or match.closed:
            return dict(id=match.id, turn=turn, rotation=rotation, placements=[])
        snapshot = match.env.clone()
        cache = getattr(match, '_hint_scores', None)
        weights = match.weights.copy()
    if cache is None or cache[0] != turn:
        with ENGINE_LOCK:
            actions, features = extract_features(snapshot, snapshot.piece.color_idx, 'clipped')
            scores = np.dot(features, weights) if len(actions) else []
        cache = (turn, {int(action): float(score) for action, score in zip(actions, scores) if np.isfinite(score)})
        with match.lock:
            if match.turn == turn and not match.closed:
                match._hint_scores = cache
    # Combine valid physical placements across every rotation. Clamped actions
    # at the right wall are deduplicated rather than counted several times.
    by_column = {}
    for action, score in cache[1].items():
        selected_rotation, column = divmod(action, 17)
        piece = snapshot.piece.clone(snapshot.world)
        piece.set_rotation(selected_rotation)
        width = (max(x for x, _ in piece.shape) + 1) * 5
        x = min(column * 5, 85 - width)
        by_column.setdefault(x // 5, {})[selected_rotation] = score
    values = [dict(column=column, x=column * 5,
                   score=float(np.mean(list(scores.values()))), rotations=len(scores))
              for column, scores in sorted(by_column.items())]
    scores = np.array([p['score'] for p in values], dtype=float)
    if len(scores):
        low, high = np.quantile(scores, [.20, .90])
        spread = float(np.ptp(scores))
        for p in values:
            if spread <= max(1.0, float(np.max(np.abs(scores)))) * 1e-10:
                p['strength'] = .12  # A tie is not evidence for a bright winner.
            else:
                rank = (np.count_nonzero(scores < p['score']) + (np.count_nonzero(scores == p['score']) - 1) / 2) / max(1, len(scores) - 1)
                scaled = float(np.clip((p['score'] - low) / (high - low), 0, 1)) if high > low else rank
                p['strength'] = float(.6 * rank + .4 * scaled)
    # Use the actual top of the settled pile, never a bounding box of a rotated
    # piece: overhangs in a piece were what made the previous glow float.
    occupied = snapshot.world != 0
    surface = np.where(occupied.any(axis=0), occupied.argmax(axis=0), 150).tolist()
    return dict(id=match.id, turn=turn, placements=values, surface=surface,
                method='Mean trained placement evaluation across valid rotations, before lookahead')
