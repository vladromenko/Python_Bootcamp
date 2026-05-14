from curses import initscr, KEY_RIGHT, KEY_LEFT, KEY_UP, KEY_DOWN, resize_term, noecho, curs_set, cbreak, endwin
from enum import Enum, auto

from consts import KEY_ESCAPE, TERM_WIDTH, TERM_HEIGHT
from domain.items import ItemObjects
from domain.utils import Direction
from presentation.objects import init_colors


class InputAction(Enum):
    TOGGLE_3D = auto()
    SAVE_GAME = auto()


class View:
    def __init__(self):
        self.stdscr = initscr()

    def user_input(self):
        input = self.stdscr.getch()
        if input == KEY_RIGHT or input == ord('d'):
            return Direction.RIGHT
        if input == KEY_LEFT or input == ord('a'):
            return Direction.LEFT
        if input == KEY_UP or input == ord('w'):
            return Direction.UP
        if input == KEY_DOWN or input == ord('s'):
            return Direction.DOWN
        if input == ord('h') or input == ord('H'):
            return ItemObjects.WEAPON
        if input == ord('j') or input == ord('J'):
            return ItemObjects.FOOD
        if input == ord('k') or input == ord('K'):
            return ItemObjects.ELIXIR
        if input == ord('e') or input == ord('E'):
            return ItemObjects.SCROLL
        if input == KEY_ESCAPE or input == ord('q') or input == ord('Q'):
            return False
        if input == ord('t') or input == ord('T'):
            return InputAction.TOGGLE_3D
        if input == ord('p') or input == ord('P'):
            return InputAction.SAVE_GAME
        if input == ord('y') or input == ord('Y'):
            return ItemObjects.KEY
        return True

    def init_view(self):
        resize_term(TERM_HEIGHT, TERM_WIDTH)
        noecho()
        cbreak()
        curs_set(False)
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)
        init_colors()

    def deinit_view(self):
        endwin()
