from random import randint, shuffle, choice

from consts import *
from domain.characters.enemy import StatType
from domain.characters.enemy_types import generate_monster_data
from domain.items import Treasure, Key, ItemObjects, Scroll, Elixir, Food, Weapon
from domain.level.places import Room, Corridor
from domain.utils import Position, make_sets, find_set, union_sets, Edge, DoorColor


class Level:
    def __init__(self):
        self._level_num = 0
        self._map = []
        self._rooms = []
        self._corridors = []
        self._monsters = []
        self._end_of_level = Position(0, 0)

    @property
    def level_num(self):
        return self._level_num

    @level_num.setter
    def level_num(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        self._level_num = value

    @property
    def end_of_level(self):
        return self._end_of_level

    @end_of_level.setter
    def end_of_level(self, value):
        if not isinstance(value, Position):
            raise ValueError("Value must be of type Position")
        self._end_of_level = value

    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, value):
        if not isinstance(value, list):
            raise ValueError("Value must be of type list")
        self._map = value

    @property
    def rooms(self):
        return self._rooms

    @rooms.setter
    def rooms(self, value):
        if not isinstance(value, list):
            raise ValueError("Value must be of type list")
        self._rooms = value

    @property
    def corridors(self):
        return self._corridors

    @corridors.setter
    def corridors(self, value):
        if not isinstance(value, list):
            raise ValueError("Value must be of type list")
        self._corridors = value

    @property
    def monsters(self):
        return self._monsters

    @monsters.setter
    def monsters(self, value):
        if not isinstance(value, list):
            raise ValueError("Value must be of type list")
        self._monsters = value

    def generate_rooms(self):
        rooms = []
        for room_count in range(ROOMS_NUM):
            room = Room().generate_room(room_count)
            rooms.append(room)
        self.rooms = rooms

    def _get_by_coord(self, coords, place):
        x = coords.x
        y = coords.y
        for i in range(len(place)):
            x_place = place[i].coords.x
            y_place = place[i].coords.y
            width = place[i].width
            height = place[i].height

            check_x = (x > x_place) and (x < x_place + width - 1)
            check_y = (y > y_place) and (y < y_place + height - 1)
            if check_x and check_y:
                return place[i]
        return None

    def is_place_by_coord(self, coords):
        if self.get_place_by_coord(coords):
            return True
        else:
            return False

    def get_place_by_coord(self, coords):
        place = self.get_room_by_coord(coords)
        if not place:
            place = self.get_corridor_by_coord(coords)
        return place

    def get_room_for_doors_by_coord(self, coords):
        x = coords.x
        y = coords.y
        for i in range(ROOMS_NUM):
            x_room = self.rooms[i].coords.x
            y_room = self.rooms[i].coords.y
            width = self.rooms[i].width
            height = self.rooms[i].height

            check_x = (x >= x_room) and (x < x_room + width)
            check_y = (y >= y_room) and (y < y_room + height)
            if check_x and check_y:
                return self.rooms[i]
        return None

    def is_door_coord(self, coords):
        if self.get_corridor_by_coord(coords) and self.get_room_for_doors_by_coord(coords):
            return True
        return False

    def get_room_by_coord(self, coords):
        return self._get_by_coord(coords, self.rooms)

    def get_corridor_by_coord(self, coords):
        return self._get_by_coord(coords, self.corridors)

    def throw_weapon(self, thrown_weapon, coords):
        place = self.get_place_by_coord(coords)
        coords_to_throw = [Position(coords.x - 1, coords.y), Position(coords.x + 1, coords.y),
                           Position(coords.x, coords.y - 1), Position(coords.x, coords.y + 1)]
        for coords in coords_to_throw:
            unoccupied = self.check_unoccupied_level(coords)
            place = self.get_place_by_coord(coords)
            if not place:
                continue
            if unoccupied:
                break
        thrown_weapon.coords = coords
        place.items.append(thrown_weapon)

    def _add_door(self, coords, door_color=DoorColor.NONE):
        room = self.get_room_for_doors_by_coord(coords)
        corridor = self.get_corridor_by_coord(coords)

        if room and corridor:
            # Добавляем дверь в обе структуры
            room.doors.append((coords, door_color))
            corridor.doors.append((coords, door_color))

            # Если дверь цветная - она изначально закрыта
            if door_color != DoorColor.NONE:
                room.lock_door(coords, door_color)
                corridor.lock_door(coords, door_color)
            return True
        return False

    def is_door_locked(self, coords):
        place = self.get_place_by_coord(coords)
        if place and hasattr(place, 'is_door_locked_at'):
            return place.is_door_locked_at(coords)
        return False

    def get_door_color(self, coords):
        place = self.get_place_by_coord(coords)
        if place:
            # Сначала проверяем список дверей
            for door_coords, color in place.doors:
                if door_coords == coords:
                    return color
            # Если не нашли в списке дверей, проверяем закрытые двери
            if hasattr(place, 'get_door_color_at'):
                return place.get_door_color_at(coords)
        return DoorColor.NONE

    def unlock_door(self, coords, door_color):
        room = self.get_room_for_doors_by_coord(coords)
        corridor = self.get_corridor_by_coord(coords)

        if room and corridor:
            # Проверяем, что дверь закрыта и цвет совпадает
            room_door_color = room.get_door_color_at(coords)
            corridor_door_color = corridor.get_door_color_at(coords)

            if (room_door_color == door_color and
                    corridor_door_color == door_color and
                    door_color != DoorColor.NONE):
                # Открываем дверь с обеих сторон
                room.unlock_door(coords)
                corridor.unlock_door(coords)
                return True
        return False

    def _generate_horizontal_corridor(self, first_room, second_room, rooms):
        first_coords = rooms[first_room].coords
        second_coords = rooms[second_room].coords

        # Для первой комнаты фиксируется правая стена, поэтому X координата определяется однозначно
        # Для Y координаты определяются возможные значения и среди них выбирается случайное
        first_x = first_coords.x + rooms[first_room].width - 1
        up_range_coord = first_coords.y + 1
        bottom_range_coord = first_coords.y + rooms[first_room].height - 2
        first_y = randint(up_range_coord, bottom_range_coord)

        # Аналогично для второй комнаты с левой стеной
        second_x = second_coords.x
        up_range_coord = second_coords.y + 1
        bottom_range_coord = second_coords.y + rooms[second_room].height - 2
        second_y = randint(up_range_coord, bottom_range_coord)

        # Если Y координаты равны, то строится прямой коридор, иначе с изгибом,
        # место которого выбирается случайно
        if first_y == second_y:
            self._create_corridor(first_x, first_y, abs(second_x - first_x) + 1, 1)
        else:
            vertical = randint(min(first_x, second_x) + 1, max(first_x, second_x) - 1)
            self._create_corridor(first_x, first_y, abs(vertical - first_x) + 1, 1)
            self._create_corridor(vertical, min(first_y, second_y), 1, abs(second_y - first_y) + 1)
            self._create_corridor(vertical, second_y, abs(second_x - vertical) + 1, 1)

        door_color = DoorColor.NONE
        colored_chance = min(15 + self.level_num * 3, 45)
        if randint(1, 100) <= colored_chance:
            door_color_name = choice(DOOR_TYPES)
            door_color = DoorColor[door_color_name]

        # Создаем координаты для дверей
        door1_coords = Position(first_x, first_y)
        door2_coords = Position(second_x, second_y)

        # Добавляем двери в коридор
        for corridor in self.corridors:
            if (corridor.coords.x <= door1_coords.x <= corridor.coords.x + corridor.width and
                    corridor.coords.y <= door1_coords.y <= corridor.coords.y + corridor.height):
                corridor.doors.append((door1_coords, door_color))
                break

        for corridor in self.corridors:
            if (corridor.coords.x <= door2_coords.x <= corridor.coords.x + corridor.width and
                    corridor.coords.y <= door2_coords.y <= corridor.coords.y + corridor.height):
                corridor.doors.append((door2_coords, door_color))
                break

        # Также добавляем в комнаты
        self._add_door(door1_coords, door_color)
        self._add_door(door2_coords, door_color)

    def _generate_vertical_corridor(self, first_room, second_room, rooms):
        first_coords = rooms[first_room].coords
        second_coords = rooms[second_room].coords

        # Для первой комнаты фиксируется нижняя стена, поэтому Y координата определяется однозначно
        # Для X координаты определяются возможные значения и среди них выбирается случайное
        first_y = first_coords.y + rooms[first_room].height - 1
        up_range_coord = first_coords.x + 1
        bottom_range_coord = first_coords.x + rooms[first_room].width - 2
        first_x = randint(up_range_coord, bottom_range_coord)

        # Аналогично для второй комнаты с верхней стеной
        second_y = second_coords.y
        up_range_coord = second_coords.x + 1
        bottom_range_coord = second_coords.x + rooms[second_room].width - 2
        second_x = randint(up_range_coord, bottom_range_coord)

        # Если X координаты равны, то строится прямой коридор, иначе с изгибом,
        # место которого выбирается случайно
        if first_x == second_x:
            self._create_corridor(first_x, first_y, 1, abs(second_y - first_y) + 1)
        else:
            horizont = randint(min(first_y, second_y) + 1, max(first_y, second_y) - 1)
            self._create_corridor(first_x, first_y, 1, abs(horizont - first_y) + 1)
            self._create_corridor(min(first_x, second_x), horizont, abs(second_x - first_x) + 1, 1)
            self._create_corridor(second_x, horizont, 1, abs(second_y - horizont) + 1)

        door_color = DoorColor.NONE
        colored_chance = min(15 + self.level_num * 3, 45)
        if randint(1, 100) <= colored_chance:
            door_color_name = choice(DOOR_TYPES)
            door_color = DoorColor[door_color_name]

        # Создаем координаты для дверей
        door1_coords = Position(first_x, first_y)
        door2_coords = Position(second_x, second_y)

        # Добавляем двери в коридор
        for corridor in self.corridors:
            if (corridor.coords.x <= door1_coords.x <= corridor.coords.x + corridor.width and
                    corridor.coords.y <= door1_coords.y <= corridor.coords.y + corridor.height):
                corridor.doors.append((door1_coords, door_color))
                break

        for corridor in self.corridors:
            if (corridor.coords.x <= door2_coords.x <= corridor.coords.x + corridor.width and
                    corridor.coords.y <= door2_coords.y <= corridor.coords.y + corridor.height):
                corridor.doors.append((door2_coords, door_color))
                break

        # Также добавляем в комнаты
        self._add_door(door1_coords, door_color)
        self._add_door(door2_coords, door_color)

    def _generate_corridors(self):
        self.corridors = []
        edges = self._generate_edges_for_rooms()
        count_corridors = len(edges)
        shuffle(edges)

        # Коридоры между комнатами будут создаваться при помощи системы непересекающихся множеств
        # Будет сделан проход по всем возможным ребрам, и если очередная пара комнат не связана,
        # то между ними будет создан коридор

        parent = [0 for _ in range(ROOMS_NUM)]
        rank = [0 for _ in range(ROOMS_NUM)]
        make_sets(parent, rank, ROOMS_NUM)

        for i in range(count_corridors):
            if find_set(edges[i].u, parent) != find_set(edges[i].v, parent):
                union_sets(edges[i].u, edges[i].v, parent, rank)
                if abs(edges[i].u - edges[i].v) == 1:
                    self._generate_horizontal_corridor(edges[i].u, edges[i].v, self.rooms)
                else:
                    self._generate_vertical_corridor(edges[i].u, edges[i].v, self.rooms)

    @staticmethod
    def _generate_edges_for_rooms():
        edges = []
        count_edges = 0
        # Генерация горизонтальных ребер между комнатами
        for i in range(ROOMS_IN_HEIGHT):
            j = 0
            while j + 1 < ROOMS_IN_WIDTH and count_edges < MAX_CORRIDORS_NUM:
                current_room = i * ROOMS_IN_HEIGHT + j
                edges.append(Edge(current_room, current_room + 1))
                count_edges += 1
                j += 1

        # Генерация вертикальных ребер между комнатами
        i = 0
        while i + 1 < ROOMS_IN_HEIGHT and count_edges < MAX_CORRIDORS_NUM:
            for j in range(ROOMS_IN_WIDTH):
                current_room = i * ROOMS_IN_HEIGHT + j
                edges.append(Edge(current_room, current_room + ROOMS_IN_WIDTH))
                count_edges += 1
            i += 1
        return edges

    def _create_corridor(self, coord_x, coord_y, width, height):
        corridor = Corridor()
        corridor.coords = Position(coord_x - 1, coord_y - 1)
        corridor.width = width + 2
        corridor.height = height + 2
        self.corridors.append(corridor)

    def _generate_exit(self):
        exit_coords = Position(0, 0)
        while True:
            exit_room = randint(0, ROOMS_NUM - 1)

            if self.rooms[exit_room].start_room:
                continue

            # Увеличение идет на 2, чтобы выход не был рядом со стеной комнаты
            # во избежание случаев, когда он будет находиться прямо перед коридором
            upper_left_x = self.rooms[exit_room].coords.x + 2
            upper_left_y = self.rooms[exit_room].coords.y + 2

            # Уменьшение идет на 5, чтобы выход не был рядом со стеной комнаты
            bottom_right_x = upper_left_x + self.rooms[exit_room].width - 5
            bottom_right_y = upper_left_y + self.rooms[exit_room].height - 5

            x = randint(upper_left_x, bottom_right_x)
            y = randint(upper_left_y, bottom_right_y)

            exit_coords = Position(x, y)
            if self.rooms[exit_room].check_unoccupied_room(exit_coords):
                break
        self.end_of_level = exit_coords

    def _generate_enemies(self, balance=None):
        self.monsters = []
        monsters_strength = int(
            INIT_MONSTERS_STRENGTH_PER_LEVEL + self.level_num * COEFF_UPDATE_STRENGTH_MONSTERS_PER_LEVEL)
        if balance and balance.get("enemy_strength") is not None:
            monsters_strength = max(1, int(monsters_strength * balance.get("enemy_strength", 1.0)))

        while monsters_strength:
            room = choice(self.rooms)
            if room.start_room:
                continue

            coords = Position(0, 0)
            room.generate_coords_of_entity(coords)

            if self.check_unoccupied_level(coords):
                enemy = generate_monster_data(self.level_num, coords)
                room.monsters.append(enemy)
                self.monsters.append(enemy)
                monsters_strength -= enemy.strength
                strength_update = int(PERCENTS_UPDATE_DIFFICULTY_MONSTERS * self.level_num)
                low_updated = StatType.LOW + int(StatType.LOW * strength_update / 100)
                if monsters_strength < low_updated:
                    break

    def _door_leads_from_room(self, door_coords, room):
        return (door_coords.x == room.coords.x or
                door_coords.x == room.coords.x + room.width - 1 or
                door_coords.y == room.coords.y or
                door_coords.y == room.coords.y + room.height - 1)

    def _place_key_in_room(self, room, door_color):
        max_attempts = 50
        for attempt in range(max_attempts):
            coords = Position(0, 0)
            room.generate_coords_of_entity(coords)

            if self.check_unoccupied_level(coords):
                key = Key(door_color)
                key.coords = coords
                room.items.append(key)
                return True

        # Если не удалось найти свободное место, создаем ключ в любом месте комнаты
        print(f"Unable to find a free space for the key in the room, forcibly creating one")
        for y in range(room.coords.y + 1, room.coords.y + room.height - 1):
            for x in range(room.coords.x + 1, room.coords.x + room.width - 1):
                coords = Position(x, y)
                if self.check_unoccupied_level(coords):
                    key = Key(door_color)
                    key.coords = coords
                    room.items.append(key)
                    return True

        # Если совсем не получается, размещаем поверх существующего предмета
        if room.items:
            # Заменяем случайный предмет на ключ
            for i, item in enumerate(room.items):
                if item.type != ItemObjects.KEY:  # Не заменяем другие ключи
                    key = Key(door_color)
                    key.coords = item.coords
                    room.items[i] = key
                    return True

        # Последний вариант: создаем в углу комнаты
        coords = Position(room.coords.x + 1, room.coords.y + 1)
        key = Key(door_color)
        key.coords = coords
        room.items.append(key)
        return True

    def _validate_key_distribution(self):
        pass  # Вся логика уже в _create_keys_for_all_colored_doors

    def _create_key_at_coords(self, coords, door_color, room):
        # Если на этой клетке уже есть предмет, удаляем его
        items_to_remove = []
        for item in room.items:
            if item.coords == coords:
                items_to_remove.append(item)

        for item in items_to_remove:
            room.items.remove(item)

        # Создаем ключ
        key = Key(door_color)
        key.coords = coords
        room.items.append(key)
        return True

    def _generate_items(self, player, balance=None):
        max_items = int(MAX_CONSUMABLES_PER_ROOM - self.level_num / LEVEL_UPDATE_DIFFICULTY)
        if max_items < 1:
            max_items = 1
        bonus_items = 0
        item_classes = None
        if balance:
            bonus_items = balance.get("items_bonus", 0)
            item_classes = [Scroll, Elixir, Food, Weapon]
            if balance.get("extra_food"):
                item_classes += [Food, Food]
        max_items = max(1, max_items + bonus_items)

        # 1. ПЕРВЫМ ДЕЛОМ: Создаем ключи для всех цветных дверей
        self._create_keys_for_all_colored_doors()

        # 2. Потом создаем обычные предметы
        self._create_regular_items(player, max_items, item_classes)

    def _place_key_guaranteed(self, room, door_color):
        # Пробуем найти случайное свободное место
        for attempt in range(30):
            coords = Position(0, 0)
            room.generate_coords_of_entity(coords)

            if self.check_unoccupied_level(coords):
                return self._create_key_at_coords(coords, door_color, room)

        # Если не нашли случайное место, ищем систематически
        for y in range(room.coords.y + 1, room.coords.y + room.height - 1):
            for x in range(room.coords.x + 1, room.coords.x + room.width - 1):
                coords = Position(x, y)
                if self.check_unoccupied_level(coords):
                    return self._create_key_at_coords(coords, door_color, room)

        # В крайнем случае, создаем в углу
        coords = Position(room.coords.x + 1, room.coords.y + 1)
        return self._create_key_at_coords(coords, door_color, room)

    def _create_keys_for_all_colored_doors(self):
        start_room = self._get_start_room()
        if not start_room:
            return
        self._ensure_start_room_has_open_exit(start_room)
        colors_in_level = self._collect_door_colors()
        if not colors_in_level:
            return
        shuffle(colors_in_level)
        unlocked_colors = set()
        for door_color in colors_in_level:
            reachable_rooms = self._get_reachable_rooms(start_room, unlocked_colors)
            target_room = self._choose_key_room(reachable_rooms, start_room)
            self._place_key_guaranteed(target_room, door_color)
            unlocked_colors.add(door_color)

    def _get_start_room(self):
        for room in self.rooms:
            if room.start_room:
                return room
        return None

    def _collect_door_colors(self):
        colors = []
        seen = set()
        for corridor in self.corridors:
            for _, door_color in corridor.doors:
                if door_color != DoorColor.NONE and door_color not in seen:
                    seen.add(door_color)
                    colors.append(door_color)
        return colors

    def _choose_key_room(self, rooms, start_room):
        if not rooms:
            return start_room
        non_start = [room for room in rooms if room is not start_room]
        if non_start:
            return choice(non_start)
        return choice(rooms)

    def _get_reachable_rooms(self, start_room, unlocked_colors):
        graph = self._build_room_graph()
        visited = {start_room}
        stack = [start_room]
        while stack:
            room = stack.pop()
            for neighbor, door_color in graph.get(room, []):
                if door_color == DoorColor.NONE or door_color in unlocked_colors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
        return list(visited)

    def _build_room_graph(self):
        graph = {room: [] for room in self.rooms}
        for corridor in self.corridors:
            rooms = []
            for door_coords, _ in corridor.doors:
                room = self.get_room_for_doors_by_coord(door_coords)
                if room and room not in rooms:
                    rooms.append(room)
            if len(rooms) < 2:
                continue
            door_color = DoorColor.NONE
            for _, color in corridor.doors:
                if color != DoorColor.NONE:
                    door_color = color
                    break
            room_a, room_b = rooms[0], rooms[1]
            graph[room_a].append((room_b, door_color))
            graph[room_b].append((room_a, door_color))
        return graph

    def _ensure_start_room_has_open_exit(self, start_room):
        if any(color == DoorColor.NONE for _, color in start_room.doors):
            return
        if not start_room.doors:
            return
        door_coords, _ = choice(start_room.doors)
        corridor = self.get_corridor_by_coord(door_coords)
        if corridor:
            self._set_corridor_door_color(corridor, DoorColor.NONE)

    def _set_corridor_door_color(self, corridor, door_color):
        for idx, (door_coords, _) in enumerate(corridor.doors):
            corridor.doors[idx] = (door_coords, door_color)
            if door_color == DoorColor.NONE:
                corridor.unlock_door(door_coords)
            else:
                corridor.lock_door(door_coords, door_color)
            room = self.get_room_for_doors_by_coord(door_coords)
            if room:
                for r_idx, (r_coords, _) in enumerate(room.doors):
                    if r_coords == door_coords:
                        room.doors[r_idx] = (r_coords, door_color)
                        if door_color == DoorColor.NONE:
                            room.unlock_door(door_coords)
                        else:
                            room.lock_door(door_coords, door_color)
                        break

    def _create_regular_items(self, player, max_items, item_classes=None):
        if not item_classes:
            item_classes = [Scroll, Elixir, Food, Weapon]

        for room in self.rooms:
            if room.start_room:
                continue

            count_items = randint(0, max_items)
            items_created = 0

            for i in range(count_items * 2):  # Даем больше попыток
                if items_created >= count_items:
                    break

                coords = Position(0, 0)
                room.generate_coords_of_entity(coords)

                if self.check_unoccupied_level(coords):
                    # Создаем ТОЛЬКО обычные предметы, НЕ ключи
                    item_class = choice(item_classes)
                    item = item_class()
                    item.coords = coords
                    item.generate_data(player)
                    room.items.append(item)
                    items_created += 1

            if count_items > 0:
                pass

    def check_unoccupied_level(self, coords):
        unoccupied = True

        # Проверяем, не закрыта ли дверь
        if self.is_door_locked(coords):
            return False

        for room in self.rooms:
            unoccupied = room.check_unoccupied_room(coords)
            if not unoccupied:
                break
        for monster in self.monsters:
            if coords == monster.coords:
                unoccupied = False
        if coords == self.end_of_level:
            unoccupied = False
        return unoccupied

    def generate_next_level(self, player, balance=None):
        self.level_num += 1
        self.generate_rooms()
        self._generate_corridors()
        player.generate_player(self.rooms)
        self._generate_exit()
        self._generate_enemies(balance)
        self._generate_items(player, balance)

        # Финальная проверка ключей
        self._validate_key_distribution()

    def is_game_ended(self):
        return True if self.level_num > MAX_GAME_LEVEL else False

    def generate_treasure(self, monster):
        price = monster.agility * LOOT_AGILITY_FACTOR + monster.health * LOOT_HP_FACTOR + monster.strength * LOOT_STRENGTH_FACTOR + randint(
            1, 20)
        treasure = Treasure()
        treasure.price = max(10, int(price))
        treasure.coords = monster.coords
        place = self.get_place_by_coord(monster.coords)
        place.items.append(treasure)

    def update_visibility(self, player):
        room = self.get_room_by_coord(player.coords)
        door = self.get_room_for_doors_by_coord(player.coords)
        corridor = self.get_corridor_by_coord(player.coords)

        if room:
            room.visible = True

            # Обнаруживаем все двери в этой комнате
            for door_coords, door_color in room.doors:
                room.discover_door(door_coords)
                # Также отмечаем в коридоре
                corridor_for_door = self.get_corridor_by_coord(door_coords)
                if corridor_for_door:
                    corridor_for_door.discover_door(door_coords)

            for corridor in self.corridors:
                if corridor.visible:
                    corridor.visible = False

        elif corridor and door:
            corridor.visible = True
            door.visible = True

            # Обнаруживаем двери в этом коридоре рядом с игроком
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    check_coords = Position(player.coords.x + dx, player.coords.y + dy)
                    # Проверяем, есть ли здесь дверь
                    for door_coords, door_color in corridor.doors:
                        if door_coords == check_coords:
                            corridor.discover_door(door_coords)
                            # Также отмечаем в комнате
                            room_for_door = self.get_room_for_doors_by_coord(door_coords)
                            if room_for_door:
                                room_for_door.discover_door(door_coords)
        elif corridor:
            corridor.visible = True
            next_corridor_coord = [Position(player.coords.x, player.coords.y + 1),
                                   Position(player.coords.x + 1, player.coords.y),
                                   Position(player.coords.x - 1, player.coords.y),
                                   Position(player.coords.x, player.coords.y - 1)]
            for coord in next_corridor_coord:
                corridor = self.get_corridor_by_coord(coord)
                if corridor:
                    corridor.visible = True

            for room in self.rooms:
                if room.visible:
                    room.visible = False

    def get_next_room(self, player):
        corridor = self.get_corridor_by_coord(player.coords)
        if not corridor:
            return False

        next_coords = player.coords
        for move in range(int(VISIBILITY_DISTANCE / 2)):
            next_coords = player.get_coords_by_direction_for(next_coords, player.direction)
            next_room = self.get_room_for_doors_by_coord(next_coords)
            door = None

            for d in corridor.doors:
                if d[0] == next_coords:
                    door = d
                    if d[1] != DoorColor.NONE:
                        for d1 in next_room.locked_doors:
                            if d1 == (next_coords.x, next_coords.y):
                                door = None
                                break
            if door:
                next_room.visible = True
                return next_room
        return None
