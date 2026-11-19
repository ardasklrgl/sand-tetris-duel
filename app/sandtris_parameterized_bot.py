import numpy as np
import ctypes
import os
from functools import lru_cache
from .sandtris_env_v10 import SandtrisEnv, GRID_WIDTH, GRID_HEIGHT, BLOCK_GRAIN, GRAIN_SIZE, COLORS, rotate_shape

class EvalFrontierResult(ctypes.Structure):
    _fields_ = [
        ("cleared", ctypes.c_int),
        ("flow", ctypes.c_float),
        ("bridge", ctypes.c_float),
        ("gap", ctypes.c_int),
        ("max_height", ctypes.c_int),
        ("bumpiness", ctypes.c_int),
        ("useful_frontier", ctypes.c_int * 5),
        ("color_gaps", ctypes.c_int * 5),
        ("valid", ctypes.c_bool)
    ]

class EvalResult(ctypes.Structure):
    _fields_ = [
        ("cleared", ctypes.c_int),
        ("gap_active", ctypes.c_int * 5),
        ("gap_blockage", ctypes.c_int * 5),
        ("max_height", ctypes.c_int),
        ("bumpiness", ctypes.c_int),
        ("comp_count", ctypes.c_int * 5),
        ("max_comp_size", ctypes.c_int * 5),
        ("exposed_pixels", ctypes.c_int * 5),
        ("valid", ctypes.c_bool)
    ]

_c_core = ctypes.CDLL(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'native', 'sandtris_c_core.so'))

_c_core.simulate_all_actions_combined.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, flags='C_CONTIGUOUS'),
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_int,
    ctypes.POINTER(EvalResult),
    ctypes.POINTER(EvalFrontierResult)
]

# The "broken" bounds that accidentally acted as hard binary thresholds
CLIPPED_BOUNDS = [
    (0, 4),      # 0. cleared (acts as binary DID I CLEAR? signal)
    (0, 150),    # 1. max_height
    (0, 2000),   # 2. bumpiness
    (0, 2.0),    # 3. flow
    (0, 2.0),    # 4. bridge (acts as binary DID I BUILD CAVE? signal)
    
    # Active Color
    (0, 85),     # 5. gap_active
    (0, 100),    # 6. gap_blockage (acts as binary IS IT FLOATING? signal)
    (0, 20),     # 7. comp_count
    (0, 4000),   # 8. max_comp_size
    (0, 500),    # 9. exposed_pixels
    (0, 300),    # 10. useful_frontier
    (0, 85),     # 11. color_gaps (shortest path gap)
    
    # Inactive O1
    (0, 85),     # 12. color_gaps O1
    (0, 100),    # 13. gap_blockage O1
    (0, 4000),   # 14. max_comp_size O1
    (0, 300),    # 15. useful_frontier O1
    
    # Inactive O2
    (0, 85),     # 16. color_gaps O2
    (0, 100),    # 17. gap_blockage O2
    (0, 4000),   # 18. max_comp_size O2
    (0, 300),    # 19. useful_frontier O2
    
    # Inactive O3
    (0, 85),     # 20. color_gaps O3
    (0, 100),    # 21. gap_blockage O3
    (0, 4000),   # 22. max_comp_size O3
    (0, 300),    # 23. useful_frontier O3
]

# The true empirical bounds to allow smooth continuous gradients
TRUE_BOUNDS = [
    (0, 2000),   # 0. cleared 
    (0, 150),    # 1. max_height
    (0, 1000),   # 2. bumpiness
    (0, 100.0),  # 3. flow 
    (0, 2000.0), # 4. bridge 
    (0, 2000),   # 5. gap_active 
    (0, 2000),   # 6. gap_blockage 
    (0, 200),    # 7. comp_count 
    (0, 4000),   # 8. max_comp_size
    (0, 500),    # 9. exposed_pixels
    (0, 300),    # 10. useful_frontier
    (0, 85),     # 11. color_gaps 
    (0, 85),     # 12. color_gaps O1
    (0, 2000),   # 13. gap_blockage O1 
    (0, 4000),   # 14. max_comp_size O1
    (0, 300),    # 15. useful_frontier O1
    (0, 85),     # 16. color_gaps O2
    (0, 2000),   # 17. gap_blockage O2
    (0, 4000),   # 18. max_comp_size O2
    (0, 300),    # 19. useful_frontier O2
    (0, 85),     # 20. color_gaps O3
    (0, 2000),   # 21. gap_blockage O3
    (0, 4000),   # 22. max_comp_size O3
    (0, 300),    # 23. useful_frontier O3
]

# Indices of heavy-tailed volume/mass features to log1p scale in 'engineered' mode
LOG_FEATURES = {0, 8, 9, 10, 14, 15, 18, 19, 22, 23}

@lru_cache(maxsize=32)
def placement_geometry(base_shape):
    """Pack each distinct drop once and map the original actions to its row."""
    columns = GRID_WIDTH // BLOCK_GRAIN
    rows = {}
    action_rows, flat_x, flat_y, sizes = [], [], [], []
    for rotation in range(4):
        shape = rotate_shape(base_shape, rotation)
        width = (max(x for x, _ in shape) + 1) * BLOCK_GRAIN
        for column in range(columns):
            x = min(column, (GRID_WIDTH - width) // BLOCK_GRAIN)
            key = tuple(sorted((x + bx, by) for bx, by in shape))
            if key not in rows:
                rows[key] = len(sizes)
                for bx, by in key:
                    for gx in range(BLOCK_GRAIN):
                        for gy in range(BLOCK_GRAIN):
                            flat_x.append(bx * BLOCK_GRAIN + gx)
                            flat_y.append(by * BLOCK_GRAIN + gy)
                sizes.append(len(key) * BLOCK_GRAIN ** 2)
            action_rows.append(rows[key])
    return (action_rows, (ctypes.c_int * len(flat_x))(*flat_x),
            (ctypes.c_int * len(flat_y))(*flat_y), (ctypes.c_int * len(sizes))(*sizes))


def extract_features(env, active_color, extraction_mode="clipped"):
    """Score drops with the requested feature normalization.

    Duplicate rotations and wall-clamped actions share a simulation. All
    original action IDs and their order are preserved for policy tie-breaking.
    """
    action_rows, c_gx, c_gy, c_num_grains = placement_geometry(tuple(env.piece.base_shape))
    num_actions = len(c_num_grains)
    c_color_idx = ctypes.c_int(active_color)
    
    out_res_base = (EvalResult * num_actions)()
    out_res_front = (EvalFrontierResult * num_actions)()
    
    c_world = np.ascontiguousarray(env.world, dtype=np.uint8)
    _c_core.simulate_all_actions_combined(c_world, num_actions, c_gx, c_gy, c_num_grains, c_color_idx, out_res_base, out_res_front)
    
    valid_actions = []
    features_list = []
    
    for action, row in enumerate(action_rows):
        if not out_res_base[row].valid or not out_res_front[row].valid:
            continue
            
        valid_actions.append(action)
        rb = out_res_base[row]
        rf = out_res_front[row]
        
        # Feature array allocation
        if extraction_mode == "binned":
            num_feats = 47
        elif extraction_mode == "engineered":
            num_feats = 27
        else:
            num_feats = 24
            
        f = np.zeros(num_feats, dtype=np.float32)
        
        f[0] = rf.cleared
        f[1] = rb.max_height
        f[2] = rb.bumpiness
        f[3] = rf.flow
        f[4] = rf.bridge
        
        f[5] = rb.gap_active[active_color]
        f[6] = rb.gap_blockage[active_color]
        f[7] = rb.comp_count[active_color]
        f[8] = rb.max_comp_size[active_color]
        f[9] = rb.exposed_pixels[active_color]
        f[10] = rf.useful_frontier[active_color]
        f[11] = rf.color_gaps[active_color]
        
        other_colors = [c for c in range(1, 5) if c != active_color]
        other_colors.sort(key=lambda c: rf.color_gaps[c])
        
        for i, oc in enumerate(other_colors):
            idx = 12 + (i * 4)
            f[idx] = rf.color_gaps[oc]
            f[idx+1] = rb.gap_blockage[oc]
            f[idx+2] = rb.max_comp_size[oc]
            f[idx+3] = rf.useful_frontier[oc]
            
        if extraction_mode == "engineered":
            f[24] = 1.0 if rf.cleared > 0 else 0.0
            f[25] = 1.0 if rf.bridge > 0 else 0.0
            f[26] = 1.0 if rb.gap_blockage[active_color] >= 1000 else 0.0
            
        elif extraction_mode == "binned":
            # 1. Clear Thresholds
            f[24] = 1.0 if rf.cleared >= 4 else 0.0
            f[25] = 1.0 if rf.cleared >= 10 else 0.0
            f[26] = 1.0 if rf.cleared >= 50 else 0.0
            f[27] = 1.0 if rf.cleared >= 100 else 0.0
            f[28] = 1.0 if rf.cleared >= 300 else 0.0
            # 2. Height Thresholds
            f[29] = 1.0 if rb.max_height > 50 else 0.0
            f[30] = 1.0 if rb.max_height > 100 else 0.0
            f[31] = 1.0 if rb.max_height > 150 else 0.0
            f[32] = 1.0 if rb.max_height > 180 else 0.0
            # 3. Bridge Thresholds
            f[33] = 1.0 if rf.bridge > 0 else 0.0
            f[34] = 1.0 if rf.bridge > 10 else 0.0
            f[35] = 1.0 if rf.bridge > 50 else 0.0
            # 4. Gap Blockage (Active)
            f[36] = 1.0 if rb.gap_blockage[active_color] > 10 else 0.0
            f[37] = 1.0 if rb.gap_blockage[active_color] > 50 else 0.0
            f[38] = 1.0 if rb.gap_blockage[active_color] >= 1000 else 0.0
            # 5. Max Component Size (Active)
            f[39] = 1.0 if rb.max_comp_size[active_color] > 100 else 0.0
            f[40] = 1.0 if rb.max_comp_size[active_color] > 500 else 0.0
            f[41] = 1.0 if rb.max_comp_size[active_color] > 1000 else 0.0
            f[42] = 1.0 if rb.max_comp_size[active_color] > 2000 else 0.0
            # 6. Bumpiness
            f[43] = 1.0 if rb.bumpiness > 10 else 0.0
            f[44] = 1.0 if rb.bumpiness > 50 else 0.0
            f[45] = 1.0 if rb.bumpiness > 100 else 0.0
            f[46] = 1.0 if rb.bumpiness > 300 else 0.0
            
        features_list.append(f)
        
    if len(valid_actions) == 0:
        return [], np.array([])
        
    feature_matrix = np.array(features_list, dtype=np.float32)
    
    # Normalize features
    bounds = TRUE_BOUNDS if extraction_mode in ["linear", "engineered", "binned"] else CLIPPED_BOUNDS
    
    for i in range(24):
        min_v, max_v = bounds[i]
        span = max_v - min_v
        
        if extraction_mode in ["engineered", "binned"] and i in LOG_FEATURES:
            # Apply log1p scaling to compress heavy-tailed features, normalized by log1p(max_v)
            feature_matrix[:, i] = np.clip(np.log1p(feature_matrix[:, i] - min_v) / np.log1p(span), 0.0, 1.0)
        else:
            feature_matrix[:, i] = np.clip((feature_matrix[:, i] - min_v) / span, 0.0, 1.0)
        
    return valid_actions, feature_matrix
    
def find_best_placement_parameterized(env, weights, extraction_mode="clipped"):
    """
    Evaluates all drops and returns the best action.
    """
    active_color = env.piece.color_idx
    valid_actions, feature_matrix = extract_features(env, active_color, extraction_mode)
    
    if len(valid_actions) == 0:
        return 0
        
    scores = np.dot(feature_matrix, weights)
    
    # Argmax over valid actions
    best_idx = np.argmax(scores)
    return valid_actions[best_idx]
