from dataclasses import dataclass

from datasource.model.board import Board


@dataclass(frozen=True)
class Game:
    game_id: str
    board: Board
