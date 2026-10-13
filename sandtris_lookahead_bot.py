import numpy as np
from sandtris_parameterized_bot import extract_features
from sandtris_env_v10 import SHAPES

def find_best_placement_color_lookahead(env, weights, k=3, extraction_mode="clipped", rng=None):
    """
    Color-Centric Expectimax Lookahead (K-Beam Search).
    Instead of assuming the next piece has the same color as the active piece,
    this evaluates how well each candidate move prepares the board for ALL 4 
    incoming colors (1: Red, 2: Blue, 3: Green, 4: Yellow).
    
    For each color, a random tetromino shape is sampled (held constant across all K
    candidates via Common Random Numbers for an unbiased, fair comparison).
    
    Expected Value = 1/4 * sum_{c=1}^4 max_{a'} Score(a' | color=c, shape=sampled_shape)
    """
    if rng is None:
        rng = np.random.default_rng()

    active_color = env.piece.color_idx
    
    # 1. Base Evaluation
    valid_actions, features_matrix = extract_features(env, active_color, extraction_mode)
    if len(valid_actions) == 0:
        return 0 # Default fallback if game is inevitably over
        
    base_scores = np.dot(features_matrix, weights)
    
    # 2. Pick top K actions
    k = min(k, len(valid_actions))
    top_k_indices = np.argsort(base_scores)[-k:][::-1]
    
    # 3. Sample a random tetromino shape for each of the 4 colors (Common Random Numbers)
    # This guarantees that all top-K candidates are benchmarked against the EXACT same incoming pieces
    test_pieces = [
        (c, SHAPES[int(rng.integers(0, len(SHAPES)))])
        for c in range(1, 5)
    ]
    
    best_overall_action = None
    best_overall_score = -np.inf
    
    # 4. Simulate future for top K actions across all 4 colors
    for idx in top_k_indices:
        action = valid_actions[idx]
        base_score = base_scores[idx]
        
        future_env = env.clone()
        obs, reward, done, _, _ = future_env.step(action)
        
        if done:
            expected_future_score = -np.inf
        else:
            total_future_score = 0.0
            for next_color, shape in test_pieces:
                future_env.piece.base_shape = list(shape)
                future_env.piece.shape = list(shape)
                future_env.piece.color_idx = next_color
                
                next_valid_actions, next_features = extract_features(future_env, next_color, extraction_mode)
                if len(next_valid_actions) > 0:
                    next_scores = np.dot(next_features, weights)
                    max_next_score = np.max(next_scores)
                    total_future_score += max_next_score
                else:
                    total_future_score -= 1000000.0 # Next piece causes unavoidable death
                    
            expected_future_score = total_future_score / len(test_pieces) # Average over 4 colors
            
        combined_score = base_score + 0.5 * expected_future_score
        
        if combined_score > best_overall_score:
            best_overall_score = combined_score
            best_overall_action = action
            
    if best_overall_action is None:
        return valid_actions[0]
        
    return best_overall_action


def find_best_placement_lookahead(env, weights, k=3, extraction_mode="clipped", lookahead_mode="shape", rng=None):
    """
    K-Beam Search Lookahead.
    - lookahead_mode="shape": Evaluates across all 7 shapes assuming active color.
    - lookahead_mode="color": Evaluates across all 4 colors with a random shape for each.
    """
    if lookahead_mode == "color":
        return find_best_placement_color_lookahead(env, weights, k=k, extraction_mode=extraction_mode, rng=rng)

    active_color = env.piece.color_idx
    
    # 1. Base Evaluation
    valid_actions, features_matrix = extract_features(env, active_color, extraction_mode)
    if len(valid_actions) == 0:
        return 0 # Default fallback if game is inevitably over
        
    base_scores = np.dot(features_matrix, weights)
    
    # 2. Pick top K actions
    k = min(k, len(valid_actions))
    top_k_indices = np.argsort(base_scores)[-k:][::-1]
    
    best_overall_action = None
    best_overall_score = -np.inf
    
    # 3. Simulate future for top K actions across 7 shapes
    for idx in top_k_indices:
        action = valid_actions[idx]
        base_score = base_scores[idx]
        
        # Clone env and step
        future_env = env.clone()
        obs, reward, done, _, _ = future_env.step(action)
        
        if done:
            expected_future_score = -np.inf
        else:
            total_future_score = 0.0
            shapes_evaluated = 0
            next_color = active_color 
            
            for shape in SHAPES:
                future_env.piece.base_shape = list(shape)
                future_env.piece.shape = list(shape)
                future_env.piece.color_idx = next_color
                
                next_valid_actions, next_features = extract_features(future_env, next_color, extraction_mode)
                if len(next_valid_actions) > 0:
                    next_scores = np.dot(next_features, weights)
                    max_next_score = np.max(next_scores)
                    total_future_score += max_next_score
                else:
                    total_future_score -= 1000000.0 # Next piece causes unavoidable death
                shapes_evaluated += 1
                
            expected_future_score = total_future_score / shapes_evaluated
            
        combined_score = base_score + 0.5 * expected_future_score
        
        if combined_score > best_overall_score:
            best_overall_score = combined_score
            best_overall_action = action
            
    if best_overall_action is None:
        return valid_actions[0]
        
    return best_overall_action

