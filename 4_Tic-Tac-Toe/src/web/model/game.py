from dataclasses import dataclass

from web.model.board import Board


@dataclass(frozen=True)
class Game:
    game_id: str
    board: Board
