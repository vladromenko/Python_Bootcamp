from abc import abstractmethod
from random import randint

from consts import INITIAL_HIT_CHANCE, STANDART_AGILITY, AGILITY_FACTOR
from domain.utils import Direction, Position


class Character:
    def __init__(self, health, agility, strength):
        self._health = health
        self._agility = agility
        self._strength = strength
        self._coords = Position(0, 0)
        self._enemies = []
        self._observers = []

    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        self._health = value

    @property
    def agility(self):
        return self._agility

    @agility.setter
    def agility(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        self._agility = value

    @property
    def strength(self):
        return self._strength

    @strength.setter
    def strength(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        self._strength = value

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, value):
        if not isinstance(value, Position):
            raise ValueError("Value must be of type Position")
        self._coords = value

    @property
    def enemies(self):
        return self._enemies

    @enemies.setter
    def enemies(self, value):
        if not isinstance(value, list):
            raise ValueError("Value must be of type list")
        self._enemies = value

    def start_battle(self, enemy):
        if enemy in self.enemies:
            return
        enemy.enemies.append(self)
        self.enemies.append(enemy)

    def end_battle(self, enemy):
        if enemy not in self.enemies:
            return
        enemy.enemies.remove(self)
        self.enemies.remove(enemy)

    def _move(self, direction: Direction):
        self.coords = self._get_coords_by_direction(direction)

    @staticmethod
    def get_coords_by_direction_for(coords, direction):
        new_x = coords.x
        new_y = coords.y
        match direction:
            case Direction.UP:
                new_y -= 1
            case Direction.DOWN:
                new_y += 1
            case Direction.RIGHT:
                new_x += 1
            case Direction.LEFT:
                new_x -= 1
            case Direction.DIAGONALLY_UP_RIGHT:
                new_y -= 1
                new_x += 1
            case Direction.DIAGONALLY_UP_LEFT:
                new_y -= 1
                new_x -= 1
            case Direction.DIAGONALLY_DOWN_RIGHT:
                new_y += 1
                new_x += 1
            case Direction.DIAGONALLY_DOWN_LEFT:
                new_y += 1
                new_x -= 1
            case Direction.STOP:
                pass
        return Position(new_x, new_y)

    def _get_coords_by_direction(self, direction):
        return Character.get_coords_by_direction_for(self.coords, direction)

    def _attack(self, target, direction: Direction):
        coords = self._get_coords_by_direction(direction)
        if coords != target.coords:
            return False
        if hasattr(target, 'first_attack') and target.first_attack:
            # первая атака missed
            target.first_attack = False
            return True
        health_before = target.health
        self._handle_attack(target)
        return True

    def _handle_attack(self, target):
        chance = INITIAL_HIT_CHANCE + (self.agility - target.agility - STANDART_AGILITY) * AGILITY_FACTOR
        if not randint(0, 100) >= chance:
            target.health -= self._calculate_damage()

    @abstractmethod
    def _calculate_damage(self):
        pass

    def check_contact(self, character):
        if (self.coords.x == character.coords.x and abs(self.coords.y - character.coords.y) == 1) or (
                self.coords.y == character.coords.y and abs(self.coords.x - character.coords.x) == 1):
            return True
        return False
