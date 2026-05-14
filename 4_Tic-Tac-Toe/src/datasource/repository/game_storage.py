from threading import Lock
from typing import Dict, Optional

from datasource.model.game import Game


class GameStorage:
    def __init__(self) -> None:
        self._lock = Lock()
        self._games: Dict[str, Game] = {}

    def save(self, game: Game) -> None:
        with self._lock:
            self._games[game.game_id] = game

    def get(self, game_id: str) -> Optional[Game]:
        with self._lock:
            return self._games.get(game_id)
