from typing import Optional

from datasource.mapper.game_mapper import from_domain, to_domain
from datasource.repository.game_storage import GameStorage
from domain.model.game import Game


class GameRepository:
    def __init__(self, storage: GameStorage) -> None:
        self._storage = storage

    def save(self, game: Game) -> Game:
        data_game = from_domain(game)
        self._storage.save(data_game)
        return game

    def get(self, game_id: str) -> Optional[Game]:
        data_game = self._storage.get(game_id)
        if data_game is None:
            return None
        return to_domain(data_game)
