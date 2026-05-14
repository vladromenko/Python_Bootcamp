from typing import List

from datasource.model.board import Board as DataBoard
from datasource.model.game import Game as DataGame
from domain.model.board import Board as DomainBoard
from domain.model.game import Game as DomainGame


def to_domain(data_game: DataGame) -> DomainGame:
    return DomainGame(
        game_id=data_game.game_id,
        board=DomainBoard(cells=_copy_cells(data_game.board.cells)),
    )


def from_domain(domain_game: DomainGame) -> DataGame:
    return DataGame(
        game_id=domain_game.game_id,
        board=DataBoard(cells=_copy_cells(domain_game.board.cells)),
    )


def _copy_cells(cells: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in cells]
