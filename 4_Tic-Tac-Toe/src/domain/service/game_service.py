from abc import ABC, abstractmethod

from domain.model.game import Game


class GameService(ABC):
    @abstractmethod
    def get_next_move(self, game: Game) -> Game:
        raise NotImplementedError

    @abstractmethod
    def validate_board(self, game: Game) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_game_over(self, game: Game) -> bool:
        raise NotImplementedError
