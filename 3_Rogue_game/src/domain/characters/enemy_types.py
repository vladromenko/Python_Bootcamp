from random import randint, choice

from consts import MAX_HP_PART, MAX_TRIES_TO_MOVE, SLEEP_CHANCE, PERCENTS_UPDATE_DIFFICULTY_MONSTERS
from domain.characters.character import Character
from domain.characters.enemy import Enemy, StatType, EnemiesObjects
from domain.utils import Direction, Position, directions_by_type


class Zombie(Enemy):
    def __init__(self):
        super().__init__(type=EnemiesObjects.ZOMBIE,
                         health=StatType.HIGH,
                         agility=StatType.LOW,
                         strength=StatType.AVERAGE,
                         hostility=StatType.AVERAGE
                         )


class Vampire(Enemy):
    def __init__(self):
        super().__init__(type=EnemiesObjects.VAMPIRE,
                         health=StatType.HIGH,
                         agility=StatType.HIGH,
                         strength=StatType.AVERAGE,
                         hostility=StatType.HIGH
                         )
        self.first_attack = True

    def _move_at_rest_by_type(self, level):
        direction = choice(directions_by_type("all"))
        if level.get_corridor_by_coord(self.coords):
            direction = choice(directions_by_type("simple"))
        return self._move_at_rest(level, direction)

    def _handle_attack(self, target):
        damage = int(target.max_health / MAX_HP_PART)
        target.max_health -= damage
        target.health -= damage


class Ghost(Enemy):
    def __init__(self):
        super().__init__(type=EnemiesObjects.GHOST,
                         health=StatType.LOW,
                         agility=StatType.HIGH,
                         strength=StatType.LOW,
                         hostility=StatType.LOW
                         )
        self._visible = True

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        if not isinstance(value, bool):
            raise ValueError("Value must be of type boolean")
        self._visible = value

    def attack(self, target, direction: Direction):
        self.visible = True
        super()._attack(target, direction)

    def _direct_move(self, target_coords, level):
        self.visible = True
        return super()._direct_move(target_coords, level)

    def _move_at_rest_by_type(self, level):
        room = level.get_room_by_coord(self.coords)
        coords = Position(0, 0)
        while True:
            room.generate_coords_of_entity(coords)

            if level.check_unoccupied_level(coords):
                self.coords = coords
                break
        self.__is_unvisible()

    def __is_unvisible(self):
        if randint(0, 1):
            self.visible = False
        else:
            self.visible = True


class Ogre(Enemy):
    def __init__(self):
        super().__init__(type=EnemiesObjects.OGRE,
                         health=StatType.VERY_HIGH,
                         agility=StatType.LOW,
                         strength=StatType.VERY_HIGH,
                         hostility=StatType.AVERAGE
                         )
        self.cooldown = False

    def _move_enemy(self, player_coords, level):
        if not self.cooldown:
            is_moved = super()._move_enemy(player_coords, level)
            return is_moved
        else:
            self.cooldown = False
        return True

    def _move_at_rest_by_type(self, level):
        path = []
        for _ in range(MAX_TRIES_TO_MOVE):
            cur_direction = choice(directions_by_type("simple"))
            coords = self._get_coords_by_direction(cur_direction)

            if level.get_room_by_coord(coords) and level.check_unoccupied_level(coords):
                coords_two_steps = Character.get_coords_by_direction_for(coords, cur_direction)
                if level.get_room_by_coord(coords_two_steps) and level.check_unoccupied_level(coords_two_steps):
                    path.append(cur_direction)
                    path.append(cur_direction)
            if path:
                break
        return path

    def _handle_attack(self, target):
        target.health -= super()._calculate_damage()

    def attack(self, target, direction: Direction):
        super()._attack(target, direction)
        self.cooldown = True


class Snake(Enemy):
    def __init__(self):
        super().__init__(type=EnemiesObjects.SNAKE,
                         health=StatType.AVERAGE,
                         agility=StatType.VERY_HIGH,
                         strength=StatType.LOW,
                         hostility=StatType.HIGH
                         )
        self.direction = Direction.STOP

    def _move_at_rest_by_type(self, level):
        while True:
            direction = choice(directions_by_type("diagonals"))
            if level.get_corridor_by_coord(self.coords):
                direction = choice(directions_by_type("simple"))
            if direction != self.direction:
                break
        self.direction = direction
        path = self._move_at_rest(level, direction)
        return path

    def _handle_attack(self, target):
        super()._handle_attack(target)
        if randint(0, 100) < SLEEP_CHANCE:
            target.__asleep = True


class Mimic(Enemy):
    def __init__(self):
        super().__init__(type=EnemiesObjects.MIMIC,
                         health=StatType.HIGH,
                         agility=StatType.HIGH,
                         strength=StatType.LOW,
                         hostility=StatType.LOW
                         )
        self.sym = choice("~efw")
        self.active = False

    def _move_at_rest_by_type(self, level):
        path = [Direction.STOP]
        return path

    def _is_player_near(self, player_coords):
        if super()._is_player_near(player_coords):
            self.active = True
            return True
        return False


def generate_monster_data(level_num, coords):
    monster = choice(Enemy.__subclasses__())()
    monster.coords = coords
    percents_update = int(PERCENTS_UPDATE_DIFFICULTY_MONSTERS * level_num)
    monster.agility += int(monster.agility * percents_update / 100)
    monster.strength += int(monster.strength * percents_update / 100)
    monster.health += int(monster.health * percents_update / 100)
    return monster
