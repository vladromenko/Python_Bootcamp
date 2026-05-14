from datalayer import save_load as storage
from datalayer.stats import normalize_session_stats, new_session_stats
from domain.characters.enemy import StatType, EnemiesObjects
from domain.characters.enemy_types import Zombie, Vampire, Ghost, Ogre, Snake, Mimic
from domain.characters.player import Player
from domain.items import ItemObjects, SubType, Treasure, Food, Elixir, Scroll, Weapon, ElixirBuff, Key
from domain.level.places import Room, Corridor
from domain.utils import Position, Direction, DoorColor
SAVE_PATH = storage.SAVE_PATH
_ENEMY_CLASS_BY_TYPE = {
    EnemiesObjects.ZOMBIE.name: Zombie,
    EnemiesObjects.VAMPIRE.name: Vampire,
    EnemiesObjects.GHOST.name: Ghost,
    EnemiesObjects.OGRE.name: Ogre,
    EnemiesObjects.SNAKE.name: Snake,
    EnemiesObjects.MIMIC.name: Mimic,
}

def save_game(player, level, session_stats, path=SAVE_PATH):
    payload = {
        "player": _player_to_dict(player),
        "level": _level_to_dict(level),
        "stats": normalize_session_stats(session_stats),
    }
    storage.save_game(payload, path)

def load_game(path=SAVE_PATH):
    data = storage.load_game(path)
    if data is None:
        return None
    player = _player_from_dict(data.get("player", {}))
    level = _level_from_dict(data.get("level", {}))
    stats = normalize_session_stats(data.get("stats", new_session_stats()))
    return player, level, stats

def load_game_into(player, level):
    loaded = load_game()
    if not loaded:
        return None
    loaded_player, loaded_level, stats = loaded
    _apply_player_state(player, loaded_player)
    _apply_level_state(level, loaded_level)
    return stats

def _player_to_dict(player):
    return {
        "name": player.name,
        "coords": _pos_to_dict(player.coords),
        "health": player.health,
        "max_health": player.max_health,
        "agility": player.agility,
        "strength": player.strength,
        "asleep": player.asleep,
        "weapon": _item_to_dict(player.weapon) if player.weapon else None,
        "elixir_buffs": [_buff_to_dict(b) for b in player.elixir_buffs],
        "backpack": {
            "foods": [_item_to_dict(i) for i in player.backpack.foods],
            "elixirs": [_item_to_dict(i) for i in player.backpack.elixirs],
            "scrolls": [_item_to_dict(i) for i in player.backpack.scrolls],
            "weapons": [_item_to_dict(i) for i in player.backpack.weapons],
            "treasures": [_item_to_dict(i) for i in player.backpack.treasures],
            # ДОБАВИМ КЛЮЧИ ИЗ РЮКЗАКА
            "keys": [_item_to_dict(i) for i in player.backpack.keys.values()],
        },
    }

def _level_to_dict(level):
    return {
        "level_num": level.level_num,
        "end_of_level": _pos_to_dict(level.end_of_level),
        "rooms": [_room_to_dict(r) for r in level.rooms],
        "corridors": [_corridor_to_dict(c) for c in level.corridors],
        "monsters": [_enemy_to_dict(m) for m in level.monsters],
    }

def _item_to_dict(item):
    payload = {"kind": item.type.name, "coords": _pos_to_dict(item.coords)}
    if item.type == ItemObjects.TREASURE:
        payload["price"] = item.price
        return payload
    payload["name"] = item.name
    payload["subtype"] = item.subtype.name
    payload["increase"] = item.increase
    if isinstance(item, Elixir):
        payload["duration"] = item.duration
    # ДОБАВИМ СОХРАНЕНИЕ ДАННЫХ КЛЮЧА
    if item.type == ItemObjects.KEY:
        payload["door_color"] = item.door_color.name  # Сохраняем цвет двери
    return payload

def _room_to_dict(room):
    return {
        "coords": _pos_to_dict(room.coords),
        "width": room.width,
        "height": room.height,
        "visible": room.visible,
        "was_visited": room.was_visited,
        "start_room": room.start_room,
        "items": [_item_to_dict(i) for i in room.items],
        # ДОБАВИМ СОХРАНЕНИЕ ДВЕРЕЙ
        "doors": [[_pos_to_dict(pos), color.name] for pos, color in room.doors],
        "locked_doors": {f"{x},{y}": color.name for (x, y), color in room.locked_doors.items()},
        "discovered_doors": [[x, y] for (x, y) in room.discovered_doors],
    }

def _corridor_to_dict(corridor):
    return {
        "coords": _pos_to_dict(corridor.coords),
        "width": corridor.width,
        "height": corridor.height,
        "visible": corridor.visible,
        "was_visited": corridor.was_visited,
        "items": [_item_to_dict(i) for i in corridor.items],
        # ДОБАВИМ СОХРАНЕНИЕ ДВЕРЕЙ ДЛЯ КОРИДОРОВ
        "doors": [[_pos_to_dict(pos), color.name] for pos, color in corridor.doors],
        "locked_doors": {f"{x},{y}": color.name for (x, y), color in corridor.locked_doors.items()},
        "discovered_doors": [[x, y] for (x, y) in corridor.discovered_doors],
    }

def _enemy_to_dict(enemy):
    payload = {
        "type": enemy.type.name,
        "coords": _pos_to_dict(enemy.coords),
        "health": enemy.health,
        "agility": enemy.agility,
        "strength": enemy.strength,
        "hostility": enemy.hostility.name,
        "extras": {},
    }
    if isinstance(enemy, Vampire):
        payload["extras"]["first_attack"] = getattr(enemy, "first_attack", False)
    if isinstance(enemy, Ghost):
        payload["extras"]["visible"] = getattr(enemy, "visible", True)
    if isinstance(enemy, Ogre):
        payload["extras"]["cooldown"] = getattr(enemy, "cooldown", False)
    if isinstance(enemy, Snake):
        payload["extras"]["direction"] = getattr(enemy, "direction", Direction.STOP).name
    if isinstance(enemy, Mimic):
        payload["extras"]["sym"] = getattr(enemy, "sym", "~")
        payload["extras"]["active"] = getattr(enemy, "active", False)
    return payload

def _corridor_from_dict(data):
    corridor = Corridor()
    corridor.coords = _pos_from_dict(data.get("coords", {}))
    corridor.width = data.get("width", 1)
    corridor.height = data.get("height", 1)
    corridor.visible = data.get("visible", False)
    corridor.was_visited = data.get("was_visited", False)
    items = _items_from_dict_list(data.get("items", []))
    corridor.items.extend(items)
    # ДОБАВИМ ЗАГРУЗКУ ДВЕРЕЙ ДЛЯ КОРИДОРОВ
    doors_data = data.get("doors", [])
    for door_data in doors_data:
        if len(door_data) == 2:
            pos_data, color_name = door_data
            pos = _pos_from_dict(pos_data)
            color = DoorColor[color_name] if color_name in DoorColor.__members__ else DoorColor.NONE
            corridor.doors.append((pos, color))
    
    # ЗАГРУЗКА ЗАКРЫТЫХ ДВЕРЕЙ
    locked_doors_data = data.get("locked_doors", {})
    for key_str, color_name in locked_doors_data.items():
        try:
            x_str, y_str = key_str.split(",")
            x, y = int(x_str), int(y_str)
            color = DoorColor[color_name] if color_name in DoorColor.__members__ else DoorColor.NONE
            corridor.locked_doors[(x, y)] = color
        except (ValueError, KeyError):
            continue
    
    # ЗАГРУЗКА ОБНАРУЖЕННЫХ ДВЕРЕЙ
    discovered_data = data.get("discovered_doors", [])
    for coords_list in discovered_data:
        if len(coords_list) == 2:
            corridor.discovered_doors.add((coords_list[0], coords_list[1]))
    return corridor

def _level_from_dict(data):
    from domain.level.level import Level
    level = Level()
    level.level_num = data.get("level_num", 0)
    level.end_of_level = _pos_from_dict(data.get("end_of_level", {}))
    level.rooms = [_room_from_dict(r) for r in data.get("rooms", [])]
    level.corridors = [_corridor_from_dict(c) for c in data.get("corridors", [])]
    level.monsters = [_enemy_from_dict(m) for m in data.get("monsters", [])]
    return level

def _player_from_dict(data):
    player = Player(data.get("name", "Player"))
    player.coords = _pos_from_dict(data.get("coords", {}))
    if isinstance(data.get("health"), int):
        player.health = data.get("health")
    if isinstance(data.get("max_health"), int):
        player.max_health = data.get("max_health")
    if isinstance(data.get("agility"), int):
        player.agility = data.get("agility")
    if isinstance(data.get("strength"), int):
        player.strength = data.get("strength")
    if isinstance(data.get("asleep"), bool):
        player.asleep = data.get("asleep")
    backpack = data.get("backpack", {})
    player.backpack.foods = _items_from_dict_list(backpack.get("foods", []))
    player.backpack.elixirs = _items_from_dict_list(backpack.get("elixirs", []))
    player.backpack.scrolls = _items_from_dict_list(backpack.get("scrolls", []))
    player.backpack.weapons = _items_from_dict_list(backpack.get("weapons", []))
    player.backpack.treasures = _items_from_dict_list(backpack.get("treasures", []))
    # ДОБАВИМ ЗАГРУЗКУ КЛЮЧЕЙ В РЮКЗАК
    keys_data = _items_from_dict_list(backpack.get("keys", []))
    for key in keys_data:
        if key and hasattr(key, 'door_color'):
            player.backpack.keys[key.door_color] = key

    weapon_data = data.get("weapon")
    weapon = _item_from_dict(weapon_data) if weapon_data else None
    if isinstance(weapon, Weapon):
        player.weapon = weapon
    player.elixir_buffs = [_buff_from_dict(b) for b in data.get("elixir_buffs", [])]
    return player

def _pos_to_dict(pos):
    return {"x": pos.x, "y": pos.y}

def _pos_from_dict(data):
    return Position(x=data.get("x", 0), y=data.get("y", 0))

def _buff_to_dict(buff):
    return {"type": buff.type.name, "increase": buff.increase, "end_time": buff.end_time}

def _buff_from_dict(data):
    buff_type = data.get("type", "HEALTH")
    increase = data.get("increase", 1)
    end_time = data.get("end_time", 1)
    return ElixirBuff(SubType[buff_type], max(1, increase), max(1, end_time))

def _items_from_dict_list(items_data):
    return [item for item in (_item_from_dict(item_data) for item_data in items_data) if item is not None]

def _item_from_dict(data):
    kind = data.get("kind")
    item = None
    if kind == ItemObjects.TREASURE.name:
        item = Treasure()
        item.price = data.get("price", 1)
    elif kind == ItemObjects.FOOD.name:
        item = Food()
    elif kind == ItemObjects.ELIXIR.name:
        item = Elixir()
    elif kind == ItemObjects.SCROLL.name:
        item = Scroll()
    elif kind == ItemObjects.WEAPON.name:
        item = Weapon()
    # ДОБАВИМ ЗАГРУЗКУ КЛЮЧА
    elif kind == ItemObjects.KEY.name:
        door_color_name = data.get("door_color", "RED")
        door_color = DoorColor[door_color_name] if door_color_name in DoorColor.__members__ else DoorColor.RED
        item = Key(door_color)
    if item is None:
        return None
    item.coords = _pos_from_dict(data.get("coords", {}))
    if kind == ItemObjects.TREASURE.name:
        return item
    item.name = data.get("name", "")
    subtype = data.get("subtype")
    if subtype in SubType.__members__:
        item.subtype = SubType[subtype]
    item.increase = data.get("increase", 1)
    if isinstance(item, Elixir):
        item.duration = data.get("duration", 1)
    return item

def _enemy_from_dict(data):
    enemy_type = data.get("type")
    enemy_class = _ENEMY_CLASS_BY_TYPE.get(enemy_type, Zombie)
    enemy = enemy_class()
    enemy.coords = _pos_from_dict(data.get("coords", {}))
    if isinstance(data.get("health"), int):
        enemy.health = data.get("health")
    if isinstance(data.get("agility"), int):
        enemy.agility = data.get("agility")
    if isinstance(data.get("strength"), int):
        enemy.strength = data.get("strength")
    if data.get("hostility") in StatType.__members__:
        enemy.hostility = StatType[data.get("hostility")]
    extras = data.get("extras", {})
    if "first_attack" in extras:
        enemy.first_attack = extras.get("first_attack")
    if "visible" in extras and isinstance(enemy, Ghost):
        enemy.visible = extras.get("visible")
    if "cooldown" in extras and isinstance(enemy, Ogre):
        enemy.cooldown = extras.get("cooldown")
    if "direction" in extras and isinstance(enemy, Snake):
        direction_name = extras.get("direction", "STOP")
        if direction_name in Direction.__members__:
            enemy.direction = Direction[direction_name]
    if isinstance(enemy, Mimic):
        if "sym" in extras:
            enemy.sym = extras.get("sym")
        if "active" in extras:
            enemy.active = extras.get("active")
    enemy.enemies = []
    return enemy

def _room_from_dict(data):
    room = Room()
    room.coords = _pos_from_dict(data.get("coords", {}))
    room.width = data.get("width", 1)
    room.height = data.get("height", 1)
    room.visible = data.get("visible", False)
    room.was_visited = data.get("was_visited", False)
    room.start_room = data.get("start_room", False)
    items = _items_from_dict_list(data.get("items", []))
    room.items.extend(items)
    # ДОБАВИМ ЗАГРУЗКУ ДВЕРЕЙ
    doors_data = data.get("doors", [])
    for door_data in doors_data:
        if len(door_data) == 2:
            pos_data, color_name = door_data
            pos = _pos_from_dict(pos_data)
            color = DoorColor[color_name] if color_name in DoorColor.__members__ else DoorColor.NONE
            room.doors.append((pos, color))
    
    # ЗАГРУЗКА ЗАКРЫТЫХ ДВЕРЕЙ
    locked_doors_data = data.get("locked_doors", {})
    for key_str, color_name in locked_doors_data.items():
        try:
            x_str, y_str = key_str.split(",")
            x, y = int(x_str), int(y_str)
            color = DoorColor[color_name] if color_name in DoorColor.__members__ else DoorColor.NONE
            room.locked_doors[(x, y)] = color
        except (ValueError, KeyError):
            continue
    
    # ЗАГРУЗКА ОБНАРУЖЕННЫХ ДВЕРЕЙ
    discovered_data = data.get("discovered_doors", [])
    for coords_list in discovered_data:
        if len(coords_list) == 2:
            room.discovered_doors.add((coords_list[0], coords_list[1]))
    room.monsters = []
    return room

def _apply_player_state(target, source):
    target.name = source.name
    target.coords = Position(source.coords.x, source.coords.y)
    target.health = source.health
    target.max_health = source.max_health
    target.agility = source.agility
    target.strength = source.strength
    target.asleep = source.asleep
    target.weapon = source.weapon
    target.elixir_buffs = list(source.elixir_buffs)
    target.enemies = []
    target.backpack.foods = list(source.backpack.foods)
    target.backpack.elixirs = list(source.backpack.elixirs)
    target.backpack.scrolls = list(source.backpack.scrolls)
    target.backpack.weapons = list(source.backpack.weapons)
    target.backpack.treasures = list(source.backpack.treasures)
    # ДОБАВИМ КЛЮЧИ
    target.backpack.keys = dict(source.backpack.keys)

def _apply_level_state(target, source):
    target.level_num = source.level_num
    target.map = [row[:] for row in source.map]
    target.rooms = list(source.rooms)
    target.corridors = list(source.corridors)
    target.monsters = list(source.monsters)
    target.end_of_level = Position(source.end_of_level.x, source.end_of_level.y)
    for room in target.rooms:
        room.monsters = []
        # Убедимся, что списки дверей инициализированы
        if not hasattr(room, 'doors'):
            room.doors = []
        if not hasattr(room, 'locked_doors'):
            room.locked_doors = {}
        if not hasattr(room, 'discovered_doors'):
            room.discovered_doors = set()

    for corridor in target.corridors:
        # Убедимся, что списки дверей инициализированы
        if not hasattr(corridor, 'doors'):
            corridor.doors = []
        if not hasattr(corridor, 'locked_doors'):
            corridor.locked_doors = {}
        if not hasattr(corridor, 'discovered_doors'):
            corridor.discovered_doors = set()

    for monster in target.monsters:
        room = target.get_room_by_coord(monster.coords)
        if room:
            room.monsters.append(monster)
