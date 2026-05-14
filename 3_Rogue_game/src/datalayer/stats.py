import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
SCOREBOARD_PATH = DATA_DIR / "scoreboard.json"
STATISTICS_PATH = DATA_DIR / "statistics.json"
_SESSION_STAT_DEFAULTS = {
    "enemies": 0,
    "food": 0,
    "elixirs": 0,
    "scrolls": 0,
    "attacks": 0,
    "missed": 0,
    "moves": 0,
}


def save_session_stat(player, level, session_stats=None):
    current_session_stat = get_current_session_stat(player, level, session_stats)
    sessions_stat = get_session_stat()
    sessions_stat["sessionStats"].append(current_session_stat)
    sessions_stat["sessionStats"].sort(key=lambda x: x.get("treasures", 0), reverse=True)
    _ensure_data_dir()
    SCOREBOARD_PATH.write_text(json.dumps(sessions_stat, indent=4), encoding="utf-8")


def get_session_stat():
    _ensure_data_dir()
    if not SCOREBOARD_PATH.exists():
        return {"sessionStats": []}
    try:
        data = json.loads(SCOREBOARD_PATH.read_text(encoding="utf-8"))
        return {"sessionStats": data.get("sessionStats", [])}
    except json.JSONDecodeError:
        return {"sessionStats": []}


def get_current_session_stat(player, level, session_stats=None):
    stats = normalize_session_stats(session_stats) if session_stats is not None else get_session_state().get_stats()
    current_session_stat = {
        "name": player.name,
        "treasures": len(player.backpack.treasures),
        "level": level.level_num,
        "enemies": stats["enemies"],
        "food": stats["food"],
        "elixirs": stats["elixirs"],
        "scrolls": stats["scrolls"],
        "attacks": stats["attacks"],
        "missed": stats["missed"],
        "moves": stats["moves"],
    }
    return current_session_stat


def get_current_session_stats():
    return get_session_state().get_stats()


def set_current_session_stats(stats):
    return get_session_state().set_stats(stats)


def reset_current_session_stats():
    return get_session_state().reset_stats()


def increment_stat(key, amount=1):
    get_session_state().increment_stat(key, amount)


def save_current_session_stats(session_stats=None):
    _ensure_data_dir()
    payload = session_stats if session_stats is not None else get_session_state().get_stats()
    STATISTICS_PATH.write_text(json.dumps(payload, indent=4), encoding="utf-8")


def normalize_session_stats(stats):
    normalized = new_session_stats()
    if isinstance(stats, dict):
        for key in normalized:
            if isinstance(stats.get(key), int):
                normalized[key] = stats.get(key, 0)
    return normalized


def new_session_stats():
    return dict(_SESSION_STAT_DEFAULTS)


class SessionState:
    def __init__(self):
        self._stats = new_session_stats()
        self._load_requested = False

    def get_stats(self):
        return self._stats

    def set_stats(self, stats):
        self._stats = normalize_session_stats(stats)
        return self._stats

    def reset_stats(self):
        return self.set_stats(new_session_stats())

    def increment_stat(self, key, amount=1):
        if key in self._stats:
            self._stats[key] += amount

    def set_load_requested(self, value):
        self._load_requested = bool(value)

    def pop_load_requested(self):
        requested = self._load_requested
        self._load_requested = False
        return requested


_SESSION_STATE = SessionState()


def get_session_state():
    return _SESSION_STATE


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
