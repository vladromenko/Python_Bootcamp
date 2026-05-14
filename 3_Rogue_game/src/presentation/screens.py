from curses import noecho, echo, KEY_UP, KEY_DOWN
from datetime import datetime

from consts import TERM_WIDTH, KEY_ESCAPE, TERM_HEIGHT
from datalayer.save_load import set_load_requested
from datalayer.stats import reset_current_session_stats


def menu_screen(stdscr, name, line):
    hello = f"HELLO, {name}!"
    align_spaces = int((32 - len(hello)) / 2)
    hello = align_spaces * ' ' + hello
    menu = [
        hello,
        "                                ",
        "           GAME  MENU           ",
        "+------------------------------+",
        "|                              |",
        "|          NEW   GAME          |",
        "|          LOAD  GAME          |",
        "|          SCOREBOARD          |",
        "|          EXIT  GAME          |",
        "|                              |",
        "+------------------------------+", ]

    width = len(menu[0])
    height = len(menu)

    (row, col) = stdscr.getmaxyx()

    shift_x = int(TERM_WIDTH / 2 - width / 1.5)
    shift_y = int((row - height) / 2)

    for i in range(height):
        stdscr.move(shift_y + i, shift_x)
        stdscr.addstr(menu[i])

    stdscr.move(shift_y + line + 5, shift_x + 5)
    stdscr.addstr(">>>")
    stdscr.move(shift_y + line + 5, shift_x + 24)
    stdscr.addstr("<<<")


def process_menu_input(stdscr, current_option):
    key = stdscr.getch()
    if key == ord('\n'):
        if current_option == 0:
            reset_current_session_stats()
            set_load_requested(False)
        elif current_option == 1:
            set_load_requested(True)
        else:
            set_load_requested(False)
        return -1
    elif key == KEY_UP or key == ord('w') or key == ord('W'):
        return max(0, current_option - 1)
    elif key == KEY_DOWN or key == ord('s') or key == ord('S'):
        return min(3, current_option + 1)
    return current_option


def display_scoreboard(stdscr, session_stat):
    stdscr.clear()

    session_stat = session_stat["sessionStats"]
    session_stat = sorted(session_stat, key=lambda x: x['treasures'], reverse=True)

    shift_x = 1
    shift_y = 1
    stdscr.move(shift_y, shift_x)
    stdscr.addstr("  Name  | treasures | level | enemies | food | elixirs | scrolls | attacks | missed | moves ")

    for session in session_stat:
        stat_str = (f"{session['name']:^10}"
                    f"{session['treasures']:^11}"
                    f"{session['level']:^9}"
                    f"{session['enemies']:^10}"
                    f"{session['food']:^6}"
                    f"{session['elixirs']:^10}"
                    f"{session['scrolls']:^10}"
                    f"{session['attacks']:^9}"
                    f"{session['missed']:^9}"
                    f"{session['moves']:^8}")
        shift_y += 2
        if shift_y >= TERM_HEIGHT - 5:
            stdscr.addstr("\n\n  Last best results")
            break
        stdscr.move(shift_y, shift_x)
        stdscr.addstr(stat_str)

    if not session_stat:
        stdscr.addstr("\n\n  No statistics yet...")
    stdscr.addstr("\n\n  Press ESCAPE key to continue...")
    while int(stdscr.getch()) != KEY_ESCAPE:
        continue
    stdscr.clear()


def get_name_screen(stdscr):
    echo()
    name = ""
    shift_x = 2
    shift_y = 1
    while name == "":
        stdscr.move(shift_y, shift_x)
        stdscr.addstr("Rogue`s Name? ")
        name = stdscr.getstr().decode('utf-8')

    stdscr.clear()
    noecho()
    return name


def print_dead_screen(stdscr, player):
    stdscr.clear()
    name = player.name
    align_spaces_name = int((30 - len(name)) / 2)
    name_aligned = "  |" + align_spaces_name * ' ' + name + (align_spaces_name + len(name) % 2) * ' ' + "|"

    if not player.enemies:
        monster_aligned = "  |          a monster           |"
    else:
        monster = player.enemies[-1].type.name
        align_spaces_monster = int((30 - len(monster) - 2) / 2)
        monster_aligned = "  |" + align_spaces_monster * ' ' + 'a ' + monster + (
                align_spaces_monster + len(monster) % 2) * ' ' + "|"
    date = datetime.now().strftime('%d-%b-%Y')
    date_aligned = "  |" + 9 * ' ' + date + 10 * ' ' + "|"
    dead_screen = [
        "  +------------------------------+",
        "  |                              |",
        "  |             REST             |",
        "  |              IN              |",
        "  |            PEACE             |",
        "  |                              |",
        f"{name_aligned}",
        "  |          killed by           |",
        f"{monster_aligned}",
        "  |                              |",
        "  |                              |",
        f"{date_aligned}",
        "  |                              |",
        "__\\/(\/)/(\/ \\(//)\)\/(//)\\)//(\//__",
        "",
        "",
        "",
        "  Press ESCAPE key to continue...",
    ]

    width = len(dead_screen[0])
    height = len(dead_screen)

    (row, col) = stdscr.getmaxyx()

    shift_x = int((col - width) / 2)
    shift_y = int((row - height) / 2)

    for i in range(height):
        stdscr.move(shift_y + i, shift_x)
        stdscr.addstr(dead_screen[i])

    while int(stdscr.getch()) != KEY_ESCAPE:
        continue
    stdscr.clear()


def print_win_screen(stdscr, player, session_stat):
    stdscr.clear()
    name = player.name
    (row, col) = stdscr.getmaxyx()
    shift_x = int((col - 30) / 2)
    shift_y = int((row - 10) / 2)
    stdscr.move(shift_y, shift_x)
    stdscr.addstr(f"CONGRATULATIONS, {name}! You have won!")
    shift_y += 1
    stdscr.move(shift_y, shift_x)

    for param in session_stat:
        shift_y += 1
        stdscr.move(shift_y, shift_x)
        stdscr.addstr(f"{param}: {session_stat[param]}")
    stdscr.move(shift_y + 3, shift_x)
    stdscr.addstr("Press ESCAPE key to continue...")
    while int(stdscr.getch()) != KEY_ESCAPE:
        continue
    stdscr.clear()


def no_item_menu(stdscr, type):
    (row, col) = stdscr.getmaxyx()
    shift_x = int((col - 30) / 2)
    shift_y = int((row - 10) / 2)
    stdscr.move(shift_y, shift_x)
    stdscr.addstr(f"You haven't any {type.name} in backpack!")
    stdscr.move(shift_y + 1, shift_x)
    stdscr.addstr("Press ESCAPE key to continue...")


def item_menu(stdscr, type, player):
    items = player.backpack.get_items_by_type(type)
    count_items = len(items)
    shift_x = 2
    shift_y = 1
    stdscr.move(shift_y, shift_x)
    stdscr.addstr(f"Choose {type.name}:")

    if type.name == 'WEAPON' and player.weapon:
        shift_y += 1
        stdscr.move(shift_y, shift_x)
        item = player.weapon
        stdscr.addstr(f"0. {item.name:<32}  +{item.increase} {item.subtype.name.lower()}")
        shift_y += 1
        stdscr.move(shift_y, shift_x)
        stdscr.addstr(f"Press 0 to put the weapon you are using back into your backpack")
        shift_y += 2
        stdscr.move(shift_y, shift_x)

    for i in range(count_items):
        subtype = items[i].subtype
        subtype_name = subtype.name.lower()
        stdscr.move(shift_y + i, shift_x)
        increase = items[i].increase
        stdscr.addstr(f"{i + 1}. {items[i].name:<32}  +{increase} {subtype_name}")

    shift_y = shift_y + count_items + 1
    stdscr.move(shift_y, shift_x)

    if count_items > 1:
        stdscr.addstr(f"Press 1-{count_items} key to choose {type.name} or ESCAPE key to continue")
    else:
        stdscr.addstr(f"Press 1 key to choose {type.name} or ESCAPE key to continue")


def print_item_menu(stdscr, player, type):
    items = player.backpack.get_items_by_type(type)
    count_items = len(items)

    stdscr.clear()
    if not count_items:
        no_item_menu(stdscr, type)
    else:
        item_menu(stdscr, type, player)


def get_item_menu_input(stdscr, player, type):
    items = player.backpack.get_items_by_type(type)
    count_items = len(items)
    while True:
        input = int(stdscr.getch())
        input_ord = int(input - ord('0'))
        if input == KEY_ESCAPE:
            stdscr.clear()
            return None
        elif 1 <= input_ord <= count_items:
            stdscr.clear()
            return input_ord
        elif input_ord == 0 and type.name == 'WEAPON':
            stdscr.clear()
            return input_ord
