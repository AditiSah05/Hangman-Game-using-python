import json
from pathlib import Path


DEFAULT_STATS = {
    "games_played": 0,
    "wins": 0,
    "losses": 0,
    "current_streak": 0,
    "best_streak": 0,
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
        for key in DEFAULT_STATS:
            value = data.get(key, DEFAULT_STATS[key])
            merged[key] = value if isinstance(value, int) and value >= 0 else DEFAULT_STATS[key]
        return merged

    def save(self, stats):
        payload = dict(DEFAULT_STATS)
        payload.update(stats)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
