from random import randint
from time import time
from types import NoneType

from consts import STRENGTH_ADDITION, STANDART_STRENGTH, STRENGTH_FACTOR, INITIAL_DAMAGE, ROOMS_NUM
from domain.backpack import Backpack
from domain.characters.character import Character
from domain.items import ItemObjects, ElixirBuff, Weapon
from domain.utils import Direction, DoorColor, Position


class PlayerObserver:
    def enemy_attacked(self, enemy, health_before):
        pass

    def item_picked(self, item):
        pass

    def item_used(self, item):
        pass

    def weapon_switched(self, item):
        pass

    def elixir_buff_is_ended(self, buff):
        pass


class Player(Character):
    def __init__(self, player_name):
        super().__init__(health=500, agility=70, strength=70)
        self._name = player_name
        self._max_health = self.health
        self._weapon = None
        self._backpack = Backpack()
        self._elixir_buffs = []
        self._asleep = False
        self._direction = Direction.STOP

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("Value must be of type str")
        if len(value) > 30:
            raise ValueError("Value must be less than 30 characters")
        self._name = value

    @property
    def max_health(self):
        return self._max_health

    @max_health.setter
    def max_health(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        self._max_health = value

    @property
    def weapon(self):
        return self._weapon

    @weapon.setter
    def weapon(self, value):
        if not isinstance(value, Weapon) and not isinstance(value, NoneType):
            raise ValueError("Value must be of type Weapon or None")
        self._weapon = value

    @property
    def backpack(self):
        return self._backpack

    @backpack.setter
    def backpack(self, value):
        if not isinstance(value, Backpack):
            raise ValueError("Value must be of type Backpack")
        self._backpack = value

    @property
    def elixir_buffs(self):
        return self._elixir_buffs

    @elixir_buffs.setter
    def elixir_buffs(self, value):
        if not isinstance(value, list):
            raise ValueError("Value must be of type list")
        self._elixir_buffs = value

    @property
    def asleep(self):
        return self._asleep

    @asleep.setter
    def asleep(self, value):
        if not isinstance(value, bool):
            raise ValueError("Value must be of type Boolean")
        self._asleep = value

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        if not isinstance(value, Direction):
            raise ValueError("Value must be of type Direction")
        self._direction = value

    def generate_player(self, rooms):
        player_room = randint(0, ROOMS_NUM - 1)
        rooms[player_room].generate_coords_of_entity(self.coords)
        rooms[player_room].start_room = True
        rooms[player_room].visible = True

    def check_death(self):
        return True if self.health <= 0 else False

    def choose_item(self, type, item_num):
        item_to_return = None
        if type == ItemObjects.WEAPON:
            if item_num == 0:
                if self.backpack.grab_item_in_backpack(self.weapon):
                    self._put_current_weapon_in_backpack()
                    return item_to_return

        if item_num:
            count_items = len(self.backpack.get_items_by_type(type))
            if count_items and 1 <= item_num <= count_items:
                item_to_return = self._use_item(type, item_num - 1)
        return item_to_return

    def _use_item(self, type, item_num):
        switched_weapon = False
        match type:
            case ItemObjects.FOOD:
                self._use_food(item_num)
            case ItemObjects.SCROLL:
                self._use_scroll(item_num)
            case ItemObjects.ELIXIR:
                self._use_elixir(item_num)
            case ItemObjects.WEAPON:
                if self.weapon:
                    switched_weapon = True
                self._change_weapon(item_num)
        item = self.backpack.remove_item_from_backpack(type, item_num)
        if switched_weapon:
            self.__notify_weapon_switched(item)
            return item
        else:
            self.__notify_item_used(item)
        return None

    def _change_weapon(self, item_num):
        self.weapon = self.backpack.weapons[item_num]

    def _put_current_weapon_in_backpack(self):
        self.__notify_item_picked(self.weapon)
        self.weapon = None

    def _use_food(self, item_num):
        food = self.backpack.foods[item_num]
        if self.health + food.increase > self._max_health:
            self.health = self._max_health
        else:
            self.health = self.health + food.increase

    def _use_scroll(self, item_num):
        scroll = self.backpack.scrolls[item_num]
        subtype_name = scroll.subtype.name
        if subtype_name == "HEALTH":
            self._max_health += scroll.increase
            self.health += scroll.increase
        elif subtype_name == "AGILITY":
            self.agility += scroll.increase
        elif subtype_name == "STRENGTH":
            self.strength += scroll.increase

    def _use_elixir(self, item_num):
        elixir = self.backpack.elixirs[item_num]
        subtype_name = elixir.subtype.name
        self.elixir_buffs.append(ElixirBuff(elixir.subtype, elixir.increase, time() + elixir.duration))
        if subtype_name == "HEALTH":
            self._max_health += elixir.increase
            self.health += elixir.increase
        elif subtype_name == "AGILITY":
            self.agility += elixir.increase
        elif subtype_name == "STRENGTH":
            self.strength += elixir.increase

    def _stop_elixir_buff(self, buff):
        buff_subtype_name = buff.type.name
        if buff_subtype_name == "HEALTH":
            self._max_health -= buff.increase
            self.health -= buff.increase
            if self.health <= 0:
                self.health = 1
        elif buff_subtype_name == "AGILITY":
            self.agility -= buff.increase
        elif buff_subtype_name == "STRENGTH":
            self.strength -= buff.increase

    def check_elixir_buff_end(self):
        for buff in self.elixir_buffs:
            if buff.end_time <= time():
                self._stop_elixir_buff(buff)
                self._elixir_buffs.remove(buff)
                self.__notify_elixir_buff_is_ended(buff)

    def _calculate_damage(self):
        if self.weapon:
            damage = self.weapon.increase * (self.strength + STRENGTH_ADDITION) / 100
        else:
            damage = INITIAL_DAMAGE + (self.strength - STANDART_STRENGTH) * STRENGTH_FACTOR
        return int(damage)

    def process_move(self, direction, level):
        if self.asleep:
            self.asleep = False
            return

        for enemy in level.monsters:
            if self.check_contact(enemy):
                self.start_battle(enemy)
        attacked = False
        for enemy in self.enemies:
            enemy_health_before = enemy.health
            if self._attack(enemy, direction):
                attacked = True
            if attacked and self._get_coords_by_direction(direction) == enemy.coords:
                self.__notify_enemy_attacked(enemy, enemy_health_before)
                if enemy.health <= 0:
                    enemy.end_battle(self)

        if not attacked:
            new_coords = self._get_coords_by_direction(direction)

            # ПРОВЕРЯЕМ И ОБНАРУЖИВАЕМ ДВЕРИ
            # Если игрок подошел вплотную к двери (соседняя клетка)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    check_coords = Position(new_coords.x + dx, new_coords.y + dy)
                    if level.is_door_coord(check_coords):
                        # Обнаруживаем дверь
                        place = level.get_place_by_coord(check_coords)
                        if place:
                            place.discover_door(check_coords)

                        # Также отмечаем в комнате
                        room = level.get_room_for_doors_by_coord(check_coords)
                        if room:
                            room.discover_door(check_coords)

            # Проверяем, не закрыта ли дверь
            if level.is_door_locked(new_coords):
                door_color = level.get_door_color(new_coords)
                if self.has_key_for_door(door_color):
                    # Открываем дверь ключом (ключ НЕ расходуется)
                    if door_color != DoorColor.NONE:
                        if level.unlock_door(new_coords, door_color):
                            self.__notify_door_unlocked(door_color)
                            # Ключ НЕ удаляется из инвентаря!
                else:
                    self.__notify_door_locked(door_color)
                    return

            if level.is_place_by_coord(new_coords):
                self._move(direction)
                self._direction = direction
                self._check_items_ui(level)

    def _check_items_ui(self, level):
        place = level.get_place_by_coord(self.coords)
        if place:
            get_consumable = place.check_consumable(self)
            if get_consumable:
                self.__notify_item_picked(get_consumable)

    def __notify_door_unlocked(self, door_color):
        for observer in self._observers:
            if hasattr(observer, 'door_unlocked'):
                observer.door_unlocked(door_color)

    def __notify_door_locked(self, door_color):
        for observer in self._observers:
            if hasattr(observer, 'door_locked'):
                observer.door_locked(door_color)

    def __notify_enemy_attacked(self, enemy, health_before):
        for i in self._observers:
            i.enemy_attacked(enemy, health_before)

    def __notify_item_picked(self, item):
        for i in self._observers:
            i.item_picked(item)

    def __notify_item_used(self, item):
        for i in self._observers:
            i.item_used(item)

    def __notify_weapon_switched(self, item):
        for i in self._observers:
            i.weapon_switched(item)

    def __notify_elixir_buff_is_ended(self, buff):
        for i in self._observers:
            i.elixir_buff_is_ended(buff)

    def has_key_for_door(self, door_color):
        """Проверить, есть ли у игрока ключ для двери"""
        if door_color == DoorColor.NONE:
            return True  # Обычные двери всегда открыты
        return self.backpack.has_key_for_color(door_color)

    def use_key(self, door_color):
        """Использовать ключ для двери (ключ остается в инвентаре)"""
        return self.backpack.use_key(door_color)
