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

            self.assertEqual(data["schema_version"], 2)
            self.assertEqual(data["player_name"], "Player")
            self.assertFalse(data["timer_enabled"])
            self.assertEqual(data["turn_seconds"], 15)
            self.assertEqual(data["hints_per_round"], 2)
            self.assertTrue(data["sound_enabled"])
            self.assertEqual(data["default_difficulty"], "medium")
            self.assertEqual(data["default_theme"], "all")
            self.assertEqual(data["games_played"], 0)
            self.assertEqual(data["achievements"], [])
            self.assertEqual(data["leaderboard"], [])
            self.assertEqual(data["round_history"], [])
            self.assertEqual(data["custom_words"], [])

    def test_load_sanitizes_invalid_payload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "stats.json"
            payload = {
                "games_played": 3,
                "wins": 2,
                "losses": -4,
                "current_streak": 1,
                "best_streak": 2,
                "player_name": "  Ada Lovelace  ",
                "timer_enabled": 1,
                "turn_seconds": 22,
                "hints_per_round": 3,
                "sound_enabled": 0,
                "default_difficulty": "hard",
                "default_theme": "custom",
                "achievements": ["First Win", 123],
                "leaderboard": [
                    {"name": "You", "score": 80, "difficulty": "hard", "theme": "tech"},
                    {"name": "Bad", "score": -1, "difficulty": "easy", "theme": "all"},
                ],
                "round_history": [
                    {"word": "PYTHON", "result": "Win", "score": 30, "difficulty": "medium", "theme": "tech"},
                    {"word": "BAD", "result": "Loss", "score": -2, "difficulty": "easy", "theme": "all"},
                ],
                "custom_words": [
                    {"word": "planet", "hint": "world"},
                    {"word": "1bad", "hint": "skip"},
                ],
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            store = StatsStore(path)

            data = store.load()

            self.assertEqual(data["schema_version"], 2)
            self.assertEqual(data["player_name"], "Ada Lovelace")
            self.assertTrue(data["timer_enabled"])
            self.assertEqual(data["turn_seconds"], 22)
            self.assertEqual(data["hints_per_round"], 3)
            self.assertFalse(data["sound_enabled"])
            self.assertEqual(data["default_difficulty"], "hard")
            self.assertEqual(data["default_theme"], "custom")
            self.assertEqual(data["losses"], 0)
            self.assertEqual(data["achievements"], ["First Win"])
            self.assertEqual(len(data["leaderboard"]), 1)
            self.assertEqual(data["leaderboard"][0]["score"], 80)
            self.assertEqual(len(data["round_history"]), 1)
            self.assertEqual(data["round_history"][0]["word"], "PYTHON")
            self.assertEqual(data["custom_words"], [{"word": "PLANET", "hint": "world"}])


if __name__ == "__main__":
    unittest.main()
