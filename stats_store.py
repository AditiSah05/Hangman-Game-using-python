import json
from pathlib import Path


DEFAULT_STATS = {
    "schema_version": 2,
    "player_name": "Player",
    "timer_enabled": False,
    "turn_seconds": 15,
    "hints_per_round": 2,
    "sound_enabled": True,
    "default_difficulty": "medium",
    "default_theme": "all",
    "games_played": 0,
    "wins": 0,
    "losses": 0,
    "current_streak": 0,
    "best_streak": 0,
    "achievements": [],
    "leaderboard": [],
    "round_history": [],
    "custom_words": [],
}


class StatsStore:
    def __init__(self, path="stats.json"):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return dict(DEFAULT_STATS)

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return dict(DEFAULT_STATS)

        merged = dict(DEFAULT_STATS)
        merged["schema_version"] = 2

        player_name = data.get("player_name", DEFAULT_STATS["player_name"])
        if isinstance(player_name, str):
            clean_name = player_name.strip()
            merged["player_name"] = clean_name[:20] if clean_name else DEFAULT_STATS["player_name"]

        timer_enabled = data.get("timer_enabled", DEFAULT_STATS["timer_enabled"])
        merged["timer_enabled"] = bool(timer_enabled)

        turn_seconds = data.get("turn_seconds", DEFAULT_STATS["turn_seconds"])
        merged["turn_seconds"] = turn_seconds if isinstance(turn_seconds, int) and 5 <= turn_seconds <= 60 else DEFAULT_STATS["turn_seconds"]

        hints_per_round = data.get("hints_per_round", DEFAULT_STATS["hints_per_round"])
        merged["hints_per_round"] = hints_per_round if isinstance(hints_per_round, int) and 0 <= hints_per_round <= 5 else DEFAULT_STATS["hints_per_round"]

        merged["sound_enabled"] = bool(data.get("sound_enabled", DEFAULT_STATS["sound_enabled"]))

        default_difficulty = data.get("default_difficulty", DEFAULT_STATS["default_difficulty"])
        merged["default_difficulty"] = default_difficulty if isinstance(default_difficulty, str) else DEFAULT_STATS["default_difficulty"]

        default_theme = data.get("default_theme", DEFAULT_STATS["default_theme"])
        merged["default_theme"] = default_theme if isinstance(default_theme, str) else DEFAULT_STATS["default_theme"]

        int_keys = ("games_played", "wins", "losses", "current_streak", "best_streak")
        for key in int_keys:
            value = data.get(key, DEFAULT_STATS[key])
            merged[key] = value if isinstance(value, int) and value >= 0 else DEFAULT_STATS[key]

        achievements = data.get("achievements", [])
        if isinstance(achievements, list):
            merged["achievements"] = [item for item in achievements if isinstance(item, str)]

        leaderboard = data.get("leaderboard", [])
        sanitized_board = []
        if isinstance(leaderboard, list):
            for entry in leaderboard:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name", "You")
                score = entry.get("score", 0)
                level = entry.get("difficulty", "medium")
                theme = entry.get("theme", "all")
                if not isinstance(name, str) or not isinstance(score, int):
                    continue
                if score < 0:
                    continue
                if not isinstance(level, str) or not isinstance(theme, str):
                    continue
                sanitized_board.append(
                    {
                        "name": name,
                        "score": score,
                        "difficulty": level,
                        "theme": theme,
                    }
                )
        merged["leaderboard"] = sanitized_board[:10]

        history = data.get("round_history", [])
        sanitized_history = []
        if isinstance(history, list):
            for row in history:
                if not isinstance(row, dict):
                    continue
                word = row.get("word", "")
                result = row.get("result", "")
                score = row.get("score", 0)
                difficulty = row.get("difficulty", "medium")
                theme = row.get("theme", "all")
                if not isinstance(word, str) or not isinstance(result, str) or not isinstance(score, int):
                    continue
                if not isinstance(difficulty, str) or not isinstance(theme, str):
                    continue
                if score < 0:
                    continue
                sanitized_history.append(
                    {
                        "word": word[:30],
                        "result": result[:20],
                        "score": score,
                        "difficulty": difficulty,
                        "theme": theme,
                    }
                )
        merged["round_history"] = sanitized_history[:20]

        custom_words = data.get("custom_words", [])
        sanitized_custom = []
        if isinstance(custom_words, list):
            for item in custom_words:
                if not isinstance(item, dict):
                    continue
                word = item.get("word", "")
                hint = item.get("hint", "")
                if not isinstance(word, str) or not isinstance(hint, str):
                    continue
                clean_word = word.strip().upper()
                clean_hint = hint.strip()
                if len(clean_word) < 2 or not clean_word.isalpha() or not clean_hint:
                    continue
                sanitized_custom.append({"word": clean_word, "hint": clean_hint[:120]})
        merged["custom_words"] = sanitized_custom[:200]
        return merged

    def save(self, stats):
        payload = dict(DEFAULT_STATS)
        payload.update(stats)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
