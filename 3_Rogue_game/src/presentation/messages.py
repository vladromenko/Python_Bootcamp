from consts import TERM_WIDTH
from domain.items import ItemObjects
from domain.utils import DoorColor


def print_door_locked(stdscr, door_color):
    info_ui_clear(stdscr)
    if door_color == DoorColor.NONE:
        stdscr.addstr("The door is locked! You need a key.")
    else:
        stdscr.addstr(f"The {door_color.name.lower()} door is locked! You need a {door_color.name.lower()} key.")


def print_door_unlocked(stdscr, door_color):
    info_ui_clear(stdscr)
    if door_color == DoorColor.NONE:
        stdscr.addstr("You unlocked the door!")
    else:
        stdscr.addstr(f"You unlocked the {door_color.name.lower()} door using a {door_color.name.lower()} key!")


def print_key_picked(stdscr, key):
    info_ui_clear(stdscr)
    stdscr.addstr(f"You found a {key.door_color.name.lower()} key!")


def item_ui(stdscr, item):
    info_ui_clear(stdscr)
    if item.type == ItemObjects.TREASURE:
        stdscr.addstr(f"You take the {item.price} gold pieces!!!")
    elif item.type == ItemObjects.KEY:
        stdscr.addstr(f'You take the key "{item._name}"!!!')
    else:
        stdscr.addstr(f'You take the {item.type.name} "{item.name}"!!!')


def print_use_item(stdscr, item):
    info_ui_clear(stdscr)
    if item.type == ItemObjects.WEAPON:
        stdscr.addstr(f"Now you are using a {item.type.name} {item.name}!!!")
    else:
        stdscr.addstr(f"You used the {item.type.name} {item.name}!!!")


def attack_monster_ui(stdscr, monster, was_attack):
    info_ui_clear(stdscr)
    if was_attack and monster.health >= 0:
        stdscr.addstr(f"You hit {monster.type.name}!!!")
    elif was_attack and monster.health <= 0:
        stdscr.addstr(f"You killed {monster.type.name}!!!")
    else:
        stdscr.addstr("You missed...")


def print_data_about_monster_attack(stdscr, monster, was_attack):
    stdscr.move(0, int(TERM_WIDTH / 2))
    if was_attack:
        stdscr.addstr(f"{monster.type.name} attacked!!!")
    else:
        stdscr.addstr(f"{monster.type.name} missed!!!")


def info_ui_clear(stdscr):
    stdscr.move(0, 1)
    stdscr.clrtoeol()


def print_elixir_buff_end(stdscr, buff):
    info_ui_clear(stdscr)
    stdscr.addstr(f"The elixir's {buff.type.name}-boosting effect has ended!!!")


def print_backpack_is_full(stdscr, item):
    info_ui_clear(stdscr)
    if item.type == ItemObjects.KEY:
        stdscr.addstr(f"You already have a {item.door_color.name.lower()} key!")
    else:
        stdscr.addstr(f"Unable to pick up {item.name}, quantity of {item.type.name}s is at maximum.")


def print_switch_weapon(stdscr, item):
    info_ui_clear(stdscr)
    stdscr.addstr(f"Weapon switched! Now you are using {item.name}. Previous weapon was discarded.")
