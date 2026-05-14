from typing import List, Optional, Tuple

from datasource.repository.game_repository import GameRepository
from domain.model.board import Board
from domain.model.game import Game
from domain.service.game_service import GameService

EMPTY = 0
HUMAN = 1
COMPUTER = 2
BOARD_SIZE = 3


class GameServiceImpl(GameService):
    def __init__(self, repository: GameRepository) -> None:
        self._repository = repository

    def get_next_move(self, game: Game) -> Game:
        self.validate_board(game)
        if self.is_game_over(game):
            self._repository.save(game)
            return game
        move = _find_best_move(game.board.cells)
        if move is None:
            self._repository.save(game)
            return game
        updated_cells = _apply_move(game.board.cells, move, COMPUTER)
        updated_game = Game(game_id=game.game_id, board=Board(cells=updated_cells))
        self._repository.save(updated_game)
        return updated_game

    def validate_board(self, game: Game) -> None:
        cells = game.board.cells
        _validate_shape(cells)
        _validate_values(cells)
        stored = self._repository.get(game.game_id)
        prev_cells = _previous_cells(stored)
        _validate_previous_game(stored)
        added = _count_new_user_moves(prev_cells, cells)
        _validate_counts(prev_cells, cells, stored is not None, added)

    def is_game_over(self, game: Game) -> bool:
        return _is_game_over_cells(game.board.cells)


def _find_best_move(cells: List[List[int]]) -> Optional[Tuple[int, int]]:
    best_score, move = _minimax(cells, COMPUTER)
    return move


def _minimax(
    cells: List[List[int]], player: int
) -> Tuple[int, Optional[Tuple[int, int]]]:
    winner = _winner(cells)
    if winner == COMPUTER:
        return 10, None
    if winner == HUMAN:
        return -10, None
    if _is_draw(cells):
        return 0, None
    best_score = None
    best_move = None
    for move in _available_moves(cells):
        next_cells = _apply_move(cells, move, player)
        score, ignored_move = _minimax(next_cells, _other_player(player))
        best_score, best_move = _choose_score(
            player, score, move, best_score, best_move
        )
    return best_score, best_move


def _choose_score(
    player: int,
    score: int,
    move: Tuple[int, int],
    best_score: Optional[int],
    best_move: Optional[Tuple[int, int]],
) -> Tuple[int, Tuple[int, int]]:
    if best_score is None:
        return score, move
    if player == COMPUTER and score > best_score:
        return score, move
    if player == HUMAN and score < best_score:
        return score, move
    return best_score, best_move


def _available_moves(cells: List[List[int]]) -> List[Tuple[int, int]]:
    moves = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if cells[row][col] == EMPTY:
                moves.append((row, col))
    return moves


def _apply_move(
    cells: List[List[int]], move: Tuple[int, int], player: int
) -> List[List[int]]:
    row, col = move

    new_cells = []
    for r in range(BOARD_SIZE):
        new_row = []
        for c in range(BOARD_SIZE):
            new_row.append(cells[r][c])
        new_cells.append(new_row)

    new_cells[row][col] = player
    return new_cells


def _winner(cells: List[List[int]]) -> Optional[int]:
    for line in _lines(cells):
        if line[0] != EMPTY and line[0] == line[1] == line[2]:
            return line[0]
    return None


def _lines(cells: List[List[int]]) -> List[List[int]]:
    rows = [row[:] for row in cells]
    cols = [
        [cells[row_index][col_index] for row_index in range(BOARD_SIZE)]
        for col_index in range(BOARD_SIZE)
    ]
    diags = [
        [cells[i][i] for i in range(BOARD_SIZE)],
        [cells[i][BOARD_SIZE - 1 - i] for i in range(BOARD_SIZE)],
    ]
    return rows + cols + diags


def _is_game_over_cells(cells: List[List[int]]) -> bool:
    if _winner(cells) is not None:
        return True
    return _is_draw(cells)


def _is_draw(cells: List[List[int]]) -> bool:
    if _winner(cells) is not None:
        return False
    return all(value != EMPTY for row in cells for value in row)


def _other_player(player: int) -> int:
    if player == COMPUTER:
        return HUMAN
    return COMPUTER


def _validate_shape(cells: List[List[int]]) -> None:
    if not isinstance(cells, list) or len(cells) != BOARD_SIZE:
        raise ValueError("Board must be a 3x3 matrix.")
    for row in cells:
        if not isinstance(row, list) or len(row) != BOARD_SIZE:
            raise ValueError("Board must be a 3x3 matrix.")


def _validate_values(cells: List[List[int]]) -> None:
    for row in cells:
        for value in row:
            if value not in (EMPTY, HUMAN, COMPUTER):
                raise ValueError("Board contains invalid values.")


def _validate_previous_game(stored: Optional[Game]) -> None:
    if stored is not None and _is_game_over_cells(stored.board.cells):
        raise ValueError("Game is already finished.")


def _previous_cells(stored: Optional[Game]) -> List[List[int]]:
    if stored is None:
        return _empty_board()
    return _copy_cells(stored.board.cells)


def _count_new_user_moves(
    prev_cells: List[List[int]],
    new_cells: List[List[int]],
) -> int:
    added = 0
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            prev = prev_cells[row][col]
            new = new_cells[row][col]
            if prev == new:
                pass
            else:
                if prev != EMPTY:
                    raise ValueError("Previous moves cannot be changed.")
                if new != HUMAN:
                    raise ValueError("Only user moves are allowed.")
                added += 1
    return added


def _validate_counts(
    prev_cells: List[List[int]],
    new_cells: List[List[int]],
    stored_exists: bool,
    added: int,
) -> None:
    prev_human = _count_value(prev_cells, HUMAN)
    prev_computer = _count_value(prev_cells, COMPUTER)
    new_human = _count_value(new_cells, HUMAN)
    new_computer = _count_value(new_cells, COMPUTER)
    if stored_exists and prev_human != prev_computer:
        raise ValueError("Previous game state is inconsistent.")
    if not stored_exists and (prev_human != 0 or prev_computer != 0):
        raise ValueError("New game must start from empty board.")
    if added != 1:
        raise ValueError("Board must include exactly one new user move.")
    if new_human != prev_human + 1:
        raise ValueError("User move count is invalid.")
    if new_computer != prev_computer:
        raise ValueError("Computer moves cannot be changed.")


def _count_value(cells: List[List[int]], value: int) -> int:
    return sum(row.count(value) for row in cells)


def _copy_cells(cells: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in cells]


def _empty_board() -> List[List[int]]:
    return [
        [EMPTY for col_index in range(BOARD_SIZE)] for row_index in range(BOARD_SIZE)
    ]
