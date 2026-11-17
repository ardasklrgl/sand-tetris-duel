"""One-ply adversarial pieces, ranked by the full trained placement evaluator."""
import numpy as np
from .sandtris_env_v10 import SHAPES
from .sandtris_parameterized_bot import extract_features


def choose_evil_piece(env, weights, rng):
    """Caller holds ENGINE_LOCK. Search copies never advance the live piece RNG.

    Minimize the player's maximum score over the bot's 68 discrete actions.
    This is a heuristic attack, not a certificate against every human placement.
    """
    candidate = env.clone()
    worst_score = np.inf
    choices = []
    for shape_index, shape in enumerate(SHAPES):
        candidate.piece.base_shape = list(shape)
        for color in range(1, 5):
            candidate.piece.color_idx = color
            candidate.piece.set_rotation(0)
            actions, features = extract_features(candidate, color, 'clipped')
            score = float(np.max(features @ weights)) if len(actions) else -np.inf
            if np.isnan(score):
                raise ValueError('Could not evaluate an Evil piece.')
            if score < worst_score:
                worst_score, choices = score, [(shape_index, color)]
            elif score == worst_score:
                choices.append((shape_index, color))
    shape_index, color = choices[int(rng.integers(len(choices)))]
    return shape_index, color


def apply_evil_piece(env, weights, rng):
    shape_index, color = choose_evil_piece(env, weights, rng)
    env.piece.base_shape = list(SHAPES[shape_index])
    env.piece.color_idx = color
    env.piece.x = env.piece.y = 0
    env.piece.set_rotation(0)
