import copy
import unittest
from unittest.mock import patch

import numpy as np

from app.web_game import load_weights
from app.web_hints import placement_hints
from app.web_practice import PracticeMatch


class HintTests(unittest.TestCase):
    def test_combines_rotations_without_changing_game(self):
        match = PracticeMatch(2799618709, load_weights(), 100, 'human')
        for turn in range(6):
            match.move(turn, placement=dict(x=35, y=0, rotation=0))
        before = match.state()
        rng = copy.deepcopy(match.env._rng.bit_generator.state)
        search = copy.deepcopy(match.search_rng.bit_generator.state)
        hints = placement_hints(match, 6, 0)
        self.assertEqual(hints, placement_hints(match, 6, 3))
        self.assertEqual(before, match.state())
        self.assertEqual(rng, match.env._rng.bit_generator.state)
        self.assertEqual(search, match.search_rng.bit_generator.state)
        occupied = match.env.world != 0
        expected = np.where(occupied.any(axis=0), occupied.argmax(axis=0), 150).tolist()
        self.assertEqual(hints['surface'], expected)
        self.assertTrue(hints['placements'])
        self.assertTrue(all(0 <= p['strength'] <= 1 for p in hints['placements']))

    def test_equal_scores_remain_faint(self):
        match = PracticeMatch(123, np.ones(24), 10, 'human')
        actions = [0, 1, 2, 17, 18, 19]
        with patch('app.web_hints.extract_features', return_value=(actions, np.ones((6, 24)))):
            hints = placement_hints(match, 0, 0)
        self.assertTrue(all(p['strength'] < .2 for p in hints['placements']))

    def test_stale_turn_rejected_and_cache_advances(self):
        match = PracticeMatch(123, load_weights(), 10, 'human')
        placement_hints(match, 0, 0)
        match.move(0, placement=dict(x=35, y=0, rotation=0))
        with self.assertRaises(ValueError):
            placement_hints(match, 0, 0)
        self.assertEqual(placement_hints(match, 1, 0)['turn'], 1)
        self.assertEqual(match._hint_scores[0], 1)
