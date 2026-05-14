from enum import IntEnum, Enum, auto
from random import choice

from consts import MAX_TRIES_TO_MOVE, INITIAL_DAMAGE, STANDART_STRENGTH, STRENGTH_FACTOR
from domain.characters.character import Character
from domain.utils import Direction, directions_by_type


class StatType(IntEnum):
    LOW = 25
    AVERAGE = 50
    HIGH = 75
    VERY_HIGH = 100


class EnemiesObjects(Enum):
    ZOMBIE = auto()
    VAMPIRE = auto()
    GHOST = auto()
    OGRE = auto()
    SNAKE = auto()
    MIMIC = auto()


class EnemyObserver:
    def player_attacked(self, enemy, player_health_before):
        pass


class Enemy(Character):
    def __init__(self, type, health, agility, strength, hostility):
        super().__init__(health, agility, strength)
        self._type = type
        self._hostility = hostility

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if not isinstance(value, EnemiesObjects):
            raise ValueError("Value must be of type EnemiesObjects")
        self._type = value

    @property
    def hostility(self):
        return self._hostility

    @hostility.setter
    def hostility(self, value):
        if not isinstance(value, StatType):
            raise ValueError("Value must be of type StatType")
        self._hostility = value

    def _is_player_near(self, player_coords):
        distance = abs(player_coords.x - self.coords.x) + abs(player_coords.y - self.coords.y)
        return True if distance <= int(self.hostility / (StatType.LOW / 2)) else False

    def _direct_move(self, target_coords, level):
        path = []
        dy = target_coords.y - self.coords.y
        dx = target_coords.x - self.coords.x
        direction1 = Direction.DOWN if dy > 0 else Direction.UP
        direction2 = Direction.RIGHT if dx > 0 else Direction.LEFT
        if abs(dy) >= abs(dx):
            direction = direction1
        else:
            direction = direction2
        coords = self._get_coords_by_direction(direction)

        if level.is_place_by_coord(coords) and level.check_unoccupied_level(coords):
            path.append(direction)
        else:
            direction = direction1 if direction == direction2 else direction2
            coords = self._get_coords_by_direction(direction)
            if level.is_place_by_coord(coords) and level.check_unoccupied_level(coords):
                path.append(direction)
        return path

    def _move_at_rest_by_type(self, level):
        direction = choice(directions_by_type("simple"))
        path = self._move_at_rest(level, direction)
        return path

    def _move_at_rest(self, level, cur_direction):
        path = []
        for _ in range(MAX_TRIES_TO_MOVE):
            coords = self._get_coords_by_direction(cur_direction)
            if level.is_place_by_coord(coords) and level.check_unoccupied_level(coords):
                path.append(cur_direction)
            if path:
                break
        return path

    def _move_enemy(self, player_coords, level):
        path = None
        if self._is_player_near(player_coords):
            path = self._direct_move(player_coords, level)

        if not path:
            path = self._move_at_rest_by_type(level)

        if path:
            for i in range(len(path)):
                coords = self._get_coords_by_direction(path[i])
                if coords != player_coords and level.check_unoccupied_level(coords):
                    super()._move(path[i])
                    if i == len(path) - 1:
                        return True
        return False

    def _calculate_damage(self):
        return int(INITIAL_DAMAGE + (self.strength - STANDART_STRENGTH) * STRENGTH_FACTOR)

    def process_move(self, player, level):
        if self.health <= 0:
            level.monsters.remove(self)
            level.generate_treasure(self)
            return

        move = self._move_enemy(player.coords, level)

        if not move and player.check_contact(self):
            player_health_before = player.health
            path = self._direct_move(player.coords, level)
            if player not in self.enemies:
                self.start_battle(player)
            self._attack(player, path[0])
            self.__notify_player_attacked(player_health_before)

    def __notify_player_attacked(self, player_health_before):
        for i in self._observers:
            i.player_attacked(self, player_health_before)
