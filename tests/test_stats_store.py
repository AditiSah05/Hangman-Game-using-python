import json
import tempfile
import unittest
from pathlib import Path

from stats_store import StatsStore


class StatsStoreTests(unittest.TestCase):
    def test_load_returns_defaults_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            store = StatsStore(path)

            data = store.load()

            self.assertEqual(data["games_played"], 0)
            self.assertEqual(data["achievements"], [])
            self.assertEqual(data["leaderboard"], [])

    def test_load_sanitizes_invalid_payload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            payload = {
                "games_played": 3,
                "wins": 2,
                "losses": -4,
                "current_streak": 1,
                "best_streak": 2,
                "achievements": ["First Win", 123],
                "leaderboard": [
                    {"name": "You", "score": 80, "difficulty": "hard", "theme": "tech"},
                    {"name": "Bad", "score": -1, "difficulty": "easy", "theme": "all"},
                ],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            store = StatsStore(path)

            data = store.load()

            self.assertEqual(data["losses"], 0)
            self.assertEqual(data["achievements"], ["First Win"])
            self.assertEqual(len(data["leaderboard"]), 1)
            self.assertEqual(data["leaderboard"][0]["score"], 80)


if __name__ == "__main__":
    unittest.main()
