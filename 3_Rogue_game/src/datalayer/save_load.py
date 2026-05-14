import json
from pathlib import Path
from datalayer.stats import get_session_state

DATA_DIR = Path(__file__).resolve().parent / "data"
SAVE_PATH = DATA_DIR / "save.json"


def save_game(payload, path=SAVE_PATH):
    _ensure_data_dir()
    Path(path).write_text(json.dumps(payload, indent=4), encoding="utf-8")


def load_game(path=SAVE_PATH):
    _ensure_data_dir()
    path_obj = Path(path)
    if not path_obj.exists():
        return None
    try:
        data = json.loads(path_obj.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data


def set_load_requested(value):
    get_session_state().set_load_requested(value)


def pop_load_requested():
    return get_session_state().pop_load_requested()


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
