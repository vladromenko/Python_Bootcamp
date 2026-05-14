from random import randint

from consts import *
from domain.utils import Position, DoorColor


class Place:
    def __init__(self):
        self._visible = False
        self._was_visited = False
        self._width = 0
        self._height = 0
        self._coords = Position(0, 0)
        self._items = []
        self._doors = []
        self._discovered_doors = set()

    @property
    def discovered_doors(self):
        return self._discovered_doors

    @discovered_doors.setter
    def discovered_doors(self, value):
        self._discovered_doors = value

    def discover_door(self, coords):
        self._discovered_doors.add((coords.x, coords.y))

    def is_door_discovered(self, coords):
        return (coords.x, coords.y) in self._discovered_doors

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        if value:
            self._was_visited = True

    @property
    def doors(self):
        return self._doors

    @doors.setter
    def doors(self, value):
        self._doors = value

    def is_door_at(self, coords, door_color=None):
        for door_coords, color in self.doors:
            if door_coords == coords:
                if door_color is None or color == door_color:
                    return True
        return False

    @property
    def was_visited(self):
        return self._was_visited

    @was_visited.setter
    def was_visited(self, value):
        self._was_visited = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        if value <= 0:
            raise ValueError("Value must be more than 0")
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        if value <= 0:
            raise ValueError("Value must be more than 0")
        self._height = value

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, value):
        if not isinstance(value, Position):
            raise ValueError("Value must be of type Position")
        self._coords = value

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, value):
        if not isinstance(value, list):
            raise ValueError("Value must be of type list")
        self._itens = value

    def _remove_item_from_place(self, item, player):
        if item.type.name == 'WEAPON' and player.weapon is None:
            player.weapon = item
            self.items.remove(item)
            return True
        if player.backpack.grab_item_in_backpack(item):
            self.items.remove(item)
            return True
        return False

    def check_consumable(self, player):
        for item in self.items:
            if item.coords == player.coords:
                removed = self._remove_item_from_place(item, player)
                if removed:
                    return item
                break
        return None


class Room(Place):
    def __init__(self):
        super().__init__()
        self._monsters = []
        self._start_room = False
        self._locked_doors = {}

    @property
    def locked_doors(self):
        return self._locked_doors

    @locked_doors.setter
    def locked_doors(self, value):
        self._locked_doors = value

    def is_door_locked_at(self, coords):
        key = (coords.x, coords.y)
        return key in self._locked_doors

    def get_door_color_at(self, coords):
        key = (coords.x, coords.y)
        return self._locked_doors.get(key, DoorColor.NONE)

    def lock_door(self, coords, door_color):
        key = (coords.x, coords.y)
        self._locked_doors[key] = door_color

    def unlock_door(self, coords):
        key = (coords.x, coords.y)
        if key in self._locked_doors:
            del self._locked_doors[key]
            return True
        return False

    @property
    def start_room(self):
        return self._start_room

    @start_room.setter
    def start_room(self, value):
        if not isinstance(value, bool):
            raise ValueError("Value must be of type boolean")
        self._start_room = value

    @property
    def monsters(self):
        return self._monsters

    @monsters.setter
    def monsters(self, value):
        self._monsters = value

    def check_unoccupied_room(self, coords):
        # не проверяются коорд игрока
        unoccupied = True
        for item in self.items:
            if coords == item.coords:
                unoccupied = False
        return unoccupied

    def generate_room(self, room_count):
        self.width = randint(MIN_ROOM_WIDTH, MAX_ROOM_WIDTH)
        self.height = randint(MIN_ROOM_HEIGHT, MAX_ROOM_HEIGHT)
        left_range_coord = (room_count % ROOMS_IN_WIDTH) * REGION_WIDTH + 1
        right_range_coord = (room_count % ROOMS_IN_WIDTH + 1) * REGION_WIDTH - self.width - 1
        self.coords.x = randint(left_range_coord, right_range_coord)

        up_range_coord = (room_count / ROOMS_IN_WIDTH) * REGION_HEIGHT + 1
        bottom_range_coord = (room_count / ROOMS_IN_WIDTH + 1) * REGION_HEIGHT - self.height - 1
        self.coords.y = randint(int(up_range_coord), int(bottom_range_coord))
        return self

    def generate_coords_of_entity(self, coords: Position):
        upper_left_x = self.coords.x + 1
        upper_left_y = self.coords.y + 1

        # Уменьшение идет на 2, чтобы координата гарантированно была внутри комнаты
        bottom_right_x = upper_left_x + self.width - 2
        bottom_right_y = upper_left_y + self.height - 2

        coords.x = randint(upper_left_x + 1, bottom_right_x - 1)
        coords.y = randint(upper_left_y + 1, bottom_right_y - 1)


class Corridor(Place):
    def __init__(self):
        super().__init__()
        self._locked_doors = {}

    @property
    def locked_doors(self):
        return self._locked_doors

    @locked_doors.setter
    def locked_doors(self, value):
        self._locked_doors = value

    def is_door_locked_at(self, coords):
        key = (coords.x, coords.y)
        return key in self._locked_doors

    def get_door_color_at(self, coords):
        key = (coords.x, coords.y)
        return self._locked_doors.get(key, DoorColor.NONE)

    def lock_door(self, coords, door_color):
        key = (coords.x, coords.y)
        self._locked_doors[key] = door_color

    def unlock_door(self, coords):
        key = (coords.x, coords.y)
        if key in self._locked_doors:
            del self._locked_doors[key]
            return True
        return False
