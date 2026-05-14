from time import time, sleep
import math

from consts import TURN_ANGLE_STEP
from datalayer.stats import get_current_session_stat, get_session_stat, save_session_stat
from datalayer.stats import get_current_session_stats
from datalayer.stats import reset_current_session_stats, set_current_session_stats, save_current_session_stats
from datalayer.stats import increment_stat
from datalayer.save_load import pop_load_requested
from save_load_adapter import save_game, load_game_into
from domain.characters.enemy import EnemyObserver
from domain.characters.player import Player, PlayerObserver
from domain.items import ItemObjects
from domain.level.level import Level
from domain.utils import Direction

from presentation.messages import attack_monster_ui, print_data_about_monster_attack, item_ui, print_elixir_buff_end, \
    print_use_item, print_backpack_is_full, print_switch_weapon, info_ui_clear, print_door_locked, print_door_unlocked, \
    print_key_picked
from presentation.level import display_map
from presentation.screens import print_dead_screen, print_win_screen, print_item_menu, get_item_menu_input, \
    get_name_screen, menu_screen, process_menu_input, display_scoreboard
from presentation.user_input import View, InputAction


class GameController(PlayerObserver, EnemyObserver):
    def __init__(self):
        self.view = View()
        self.stdscr = self.view.stdscr
        self.player = Player(get_name_screen(self.stdscr))
        self.level = Level()
        self.is_3d_mode = False
        self.view_angle = -math.pi / 2
        self._level_stats_snapshot = None

        self.player.add_observer(self)
        self.player.backpack.add_observer(self)

    def door_locked(self, door_color):
        print_door_locked(self.stdscr, door_color)

    def door_unlocked(self, door_color):
        print_door_unlocked(self.stdscr, door_color)

    def item_picked(self, item):
        if item.type == ItemObjects.KEY:
            print_key_picked(self.stdscr, item)
        else:
            item_ui(self.stdscr, item)

    # PlayerObserver
    def enemy_attacked(self, enemy, health_before):
        attack_monster_ui(self.stdscr, enemy, enemy.health < health_before)
        if enemy.health < health_before:
            increment_stat("attacks")

    def item_used(self, item):
        print_use_item(self.stdscr, item)
        if item.type == ItemObjects.FOOD:
            increment_stat("food")
        elif item.type == ItemObjects.SCROLL:
            increment_stat("scrolls")
        elif item.type == ItemObjects.ELIXIR:
            increment_stat("elixirs")

    def weapon_switched(self, item):
        print_switch_weapon(self.stdscr, item)

    def elixir_buff_is_ended(self, buff):
        print_elixir_buff_end(self.stdscr, buff)

    # BackpackObserver
    def backpack_is_full(self, item):
        print_backpack_is_full(self.stdscr, item)

    # EnemyObserver
    def player_attacked(self, enemy, player_health_before):
        print_data_about_monster_attack(self.stdscr, enemy, self.player.health < player_health_before)
        if self.player.health < player_health_before:
            increment_stat("missed")

    def _generate_next_level(self, balance=None):
        # Очищаем ключи в рюкзаке при переходе на новый уровень
        self.player.backpack.keys.clear()
        self.level.generate_next_level(self.player, balance)
        for enemy in self.level.monsters:
            enemy.add_observer(self)
        self._level_stats_snapshot = get_current_session_stats().copy()

    def _get_level_balance(self):
        if self._level_stats_snapshot is None:
            return None
        current_stats = get_current_session_stats()
        delta = {
            key: current_stats.get(key, 0) - self._level_stats_snapshot.get(key, 0)
            for key in current_stats
        }
        hits_taken = delta.get("missed", 0)
        used_heals = delta.get("food", 0) + delta.get("elixirs", 0)
        attacks = delta.get("attacks", 0)
        if hits_taken >= 4 or used_heals >= 2:
            return {"enemy_strength": 0.85, "items_bonus": 1, "extra_food": True}
        if hits_taken == 0 and used_heals == 0 and attacks >= 6:
            return {"enemy_strength": 1.15, "items_bonus": -1}
        return None

    def _process_user_move(self, direction: Direction):
        info_ui_clear(self.stdscr)
        old_x = self.player.coords.x
        old_y = self.player.coords.y
        enemies_before = len(self.level.monsters)
        self.player.process_move(direction, self.level)
        if self.player.coords.x != old_x or self.player.coords.y != old_y:
            increment_stat("moves")
        self.level.update_visibility(self.player)
        for monster in self.level.monsters:
            monster.process_move(self.player, self.level)
        enemies_after = len(self.level.monsters)
        defeated = enemies_before - enemies_after
        if defeated > 0:
            increment_stat("enemies", defeated)
        self.player.check_elixir_buff_end()

    def _normalize_angle(self, angle):
        while angle <= -math.pi:
            angle += 2 * math.pi
        while angle > math.pi:
            angle -= 2 * math.pi
        return angle

    def _direction_from_angle(self, angle, forward):
        dx = math.cos(angle)
        dy = math.sin(angle)
        if not forward:
            dx = -dx
            dy = -dy
        if abs(dx) >= abs(dy):
            return Direction.RIGHT if dx > 0 else Direction.LEFT
        return Direction.DOWN if dy > 0 else Direction.UP

    def _process_3d_input(self, direction):
        if direction == Direction.LEFT:
            self.view_angle = self._normalize_angle(self.view_angle - TURN_ANGLE_STEP)
            return
        if direction == Direction.RIGHT:
            self.view_angle = self._normalize_angle(self.view_angle + TURN_ANGLE_STEP)
            return
        if direction == Direction.UP:
            move_dir = self._direction_from_angle(self.view_angle, True)
            self._process_user_move(move_dir)
            return
        if direction == Direction.DOWN:
            move_dir = self._direction_from_angle(self.view_angle, False)
            self._process_user_move(move_dir)
            return

    def _process_input(self):
        input = self.view.user_input()
        if isinstance(input, InputAction):
            if input == InputAction.TOGGLE_3D:
                self.is_3d_mode = not self.is_3d_mode
                self.stdscr.clear()
                self.stdscr.refresh()
                return True
            if input == InputAction.SAVE_GAME:
                save_game(self.player, self.level, get_current_session_stats())
                return True
        if isinstance(input, Direction):
            if self.is_3d_mode:
                self._process_3d_input(input)
                return True
            self._process_user_move(input)
            return True
        elif isinstance(input, ItemObjects):
            self._choose_item(input)
            return True
        else:
            return input

    def _choose_item(self, type):
        print_item_menu(self.stdscr, self.player, type)
        item_num = get_item_menu_input(self.stdscr, self.player, type)

        item = self.player.choose_item(type, item_num)
        if type == ItemObjects.WEAPON and item:
            self.level.throw_weapon(item, self.player.coords)

    def start_game(self):
        self.view.init_view()

        current_option = 0
        is_game_running = True

        menu_screen(self.stdscr, self.player.name, current_option)

        while is_game_running:
            menu_screen(self.stdscr, self.player.name, current_option)
            result = process_menu_input(self.stdscr, current_option)
            if result == -1:
                match current_option:
                    case 0:
                        is_game_running = self._game()
                        save_session_stat(self.player, self.level)
                    case 1:
                        is_game_running = self._game()
                        save_session_stat(self.player, self.level)
                    case 2:
                        session_stat = get_session_stat()
                        display_scoreboard(self.stdscr, session_stat)
                    case 3:
                        is_game_running = False
            else:
                current_option = result

        self.view.deinit_view()

    def _validate_loaded_doors(self):
        # Просто проверяем, что списки дверей инициализированы
        for room in self.level.rooms:
            if not hasattr(room, 'doors'):
                room.doors = []
            if not hasattr(room, 'locked_doors'):
                room.locked_doors = {}
            if not hasattr(room, 'discovered_doors'):
                room.discovered_doors = set()

        for corridor in self.level.corridors:
            if not hasattr(corridor, 'doors'):
                corridor.doors = []
            if not hasattr(corridor, 'locked_doors'):
                corridor.locked_doors = {}
            if not hasattr(corridor, 'discovered_doors'):
                corridor.discovered_doors = set()

    def _game(self):
        if pop_load_requested():
            loaded_stats = load_game_into(self.player, self.level)
            if loaded_stats is not None:
                set_current_session_stats(loaded_stats)
                for enemy in self.level.monsters:
                    enemy.add_observer(self)
                # ПРОВЕРЯЕМ, ЧТО ДВЕРИ КОРРЕКТНО ЗАГРУЖЕНЫ
                self._validate_loaded_doors()
                self._level_stats_snapshot = get_current_session_stats().copy()
            else:
                reset_current_session_stats()
                self._generate_next_level()
        else:
            self._generate_next_level()
        while True:
            start_time = time()
            display_map(self.stdscr, self.level, self.player, self.is_3d_mode, self.view_angle)

            if not self._process_input():
                save_game(self.player, self.level, get_current_session_stats())
                return False

            if self.player.check_death():
                print_dead_screen(self.stdscr, self.player)
                return False
            if self.player.coords == self.level.end_of_level:
                if self.level.level_num > 0:
                    save_game(self.player, self.level, get_current_session_stats())
                    save_current_session_stats(get_current_session_stat(self.player, self.level))
                balance = self._get_level_balance()
                self._generate_next_level(balance)
                if self.level.is_game_ended():
                    current_session_stat = get_current_session_stat(self.player, self.level)
                    print_win_screen(self.stdscr, self.player, current_session_stat)
                    return False

            end_time = time()
            time_to_sleep = max((33 - 1000 * int(end_time - start_time)) / 1000, 0)
            sleep(time_to_sleep)
