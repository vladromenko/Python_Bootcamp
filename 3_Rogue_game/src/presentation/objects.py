from curses import init_pair, start_color, use_default_colors, color_pair, init_color, COLOR_BLUE, COLOR_BLACK, \
    COLOR_YELLOW, COLOR_GREEN, COLOR_RED, COLOR_WHITE

from domain.characters.enemy_types import Zombie, Vampire, Ghost, Ogre, Snake, Mimic
from domain.characters.player import Player
from domain.items import Treasure, Scroll, Elixir, Food, Weapon, Key

import curses


def init_colors():
    start_color()
    use_default_colors()

    BROWN_COLOR = 8
    init_color(BROWN_COLOR, 588, 294, 0)

    init_pair(1, COLOR_WHITE, COLOR_BLACK)
    init_pair(2, COLOR_RED, COLOR_BLACK)
    init_pair(3, COLOR_GREEN, COLOR_BLACK)
    init_pair(4, COLOR_YELLOW, COLOR_BLACK)
    init_pair(5, COLOR_BLUE, COLOR_BLACK)
    init_pair(6, BROWN_COLOR, COLOR_BLACK)

    # Цвета для дверей
    init_pair(10, COLOR_RED, COLOR_BLACK)  # Красная дверь
    init_pair(11, COLOR_GREEN, COLOR_BLACK)  # Зеленая дверь
    init_pair(12, COLOR_BLUE, COLOR_BLACK)  # Синяя дверь
    init_pair(13, COLOR_YELLOW, COLOR_BLACK)  # Желтая дверь
    init_pair(14, COLOR_WHITE, COLOR_BLACK)  # Белая дверь (обычная)


def get_object_color(sym):
    match sym:
        case '@':
            return color_pair(4)
        case 'z':
            return color_pair(3)
        case 'v':
            return color_pair(2)
        case 'O':
            return color_pair(4)
        case 'E':
            return color_pair(3)
        case 'w':
            return color_pair(5)
        case 'f':
            return color_pair(6)
        case 'e':
            return color_pair(5)
        case '$':
            return color_pair(4)
        case '~':
            return color_pair(2)
        case '/':  # Обычная дверь
            return color_pair(14)
        case 'R':  # Красная дверь
            return color_pair(10)
        case 'G':  # Зеленая дверь
            return color_pair(11)
        case 'B':  # Синяя дверь
            return color_pair(12)
        case 'Y':  # Желтая дверь
            return color_pair(13)
        case 'k':  # Ключ
            return color_pair(4)  # Желтый
        # Для скрытых дверей (показываемых как стены)
        case _:
            if sym in [curses.ACS_HLINE, curses.ACS_VLINE]:
                return color_pair(1)  # Обычный цвет стен
    return color_pair(1)


def get_object_sym(object):
    if isinstance(object, Player):
        return '@'
    if isinstance(object, Zombie):
        return 'z'
    if isinstance(object, Vampire):
        return 'v'
    if isinstance(object, Ghost):
        if object.visible:
            return 'g'
        else:
            return '.'
    if isinstance(object, Ogre):
        return 'O'
    if isinstance(object, Snake):
        return 's'
    if isinstance(object, Mimic):
        if not object.active:
            return object.sym
        else:
            return 'm'
    if isinstance(object, Treasure):
        return '$'
    if isinstance(object, Scroll):
        return '~'
    if isinstance(object, Elixir):
        return 'e'
    if isinstance(object, Food):
        return 'f'
    if isinstance(object, Weapon):
        return 'w'
    if isinstance(object, Key):
        return 'k'
    return None
