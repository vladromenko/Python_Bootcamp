from typing import Any, Dict, List

from domain.model.board import Board as DomainBoard
from domain.model.game import Game as DomainGame
from web.model.board import Board as WebBoard
from web.model.game import Game as WebGame


def game_from_dict(data: Dict[str, Any], game_id: str) -> WebGame:
    if not isinstance(data, dict):
        raise ValueError("Invalid JSON body.")
    board_data = data.get("board")
    if not isinstance(board_data, dict):
        raise ValueError("Missing or invalid board.")
    cells = board_data.get("cells")
    if not isinstance(cells, list):
        raise ValueError("Missing or invalid board cells.")
    return WebGame(game_id=game_id, board=WebBoard(cells=cells))


def to_domain(web_game: WebGame) -> DomainGame:
    return DomainGame(
        game_id=web_game.game_id,
        board=DomainBoard(cells=_copy_cells(web_game.board.cells)),
    )


def from_domain(domain_game: DomainGame) -> WebGame:
    return WebGame(
        game_id=domain_game.game_id,
        board=WebBoard(cells=_copy_cells(domain_game.board.cells)),
    )


def game_to_dict(web_game: WebGame) -> Dict[str, Any]:
    return {
        "game_id": web_game.game_id,
        "board": {"cells": _copy_cells(web_game.board.cells)},
    }


def _copy_cells(cells: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in cells]
