import json
from pathlib import Path


DEFAULT_STATS = {
    "games_played": 0,
    "wins": 0,
    "losses": 0,
    "current_streak": 0,
    "best_streak": 0,
    "achievements": [],
    "leaderboard": [],
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
        return merged

    def save(self, stats):
        payload = dict(DEFAULT_STATS)
        payload.update(stats)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
