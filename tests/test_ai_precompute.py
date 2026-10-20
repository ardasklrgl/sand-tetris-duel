"""Check that bundled AI plans are ready and replay like live planning."""
import time
import unittest

from web_demo import DemoMatch, DemoServer
from web_game import Match, PRECOMPUTED_PLANS, load_weights


class PrecomputedAiTests(unittest.TestCase):
    def test_random_seed_cycle_uses_every_cached_plan_once(self):
        self.assertEqual(len(PRECOMPUTED_PLANS), 20)
        server = object.__new__(DemoServer)
        server.seed_pool = []
        selected = [server.next_seed() for _ in range(20)]
        self.assertEqual(set(selected), set(PRECOMPUTED_PLANS))

    def test_cached_moves_match_live_planning(self):
        seed = min(PRECOMPUTED_PLANS)
        weights = load_weights()
        cached = DemoMatch(seed, weights)
        live = Match(seed, weights, plan_limit=100)
        try:
            self.assertTrue(cached.state()["ready"])
            self.assertIsNone(cached.planning_future)
            for turn in range(5):
                deadline = time.monotonic() + 20
                while not live.state()["ready"] and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(live.state()["ready"])
                self.assertEqual(cached.action, live.action)
                cached_state = cached.move(turn, action=33)
                live_state = live.move(turn, action=33)
                self.assertEqual(cached_state["boards"]["ai"]["world"],
                                 live_state["boards"]["ai"]["world"])
        finally:
            cached.close()
            live.close()


if __name__ == "__main__":
    unittest.main()
