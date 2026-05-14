from enum import Enum, auto
from random import choice, randint

from consts import MAX_PERCENT_HEALTH_REGEN, MAX_PERCENT_AGILITY_INCREASE, MAX_PERCENT_STRENGTH_INCREASE, \
    MIN_ELIXIR_DURATION_SECONDS, MAX_ELIXIR_DURATION_SECONDS, MIN_INCREASE, MIN_WEAPON_STRENGTH, MAX_WEAPON_STRENGTH
from domain.utils import Position, DoorColor


class ItemObjects(Enum):
    FOOD = auto()
    ELIXIR = auto()
    SCROLL = auto()
    WEAPON = auto()
    TREASURE = auto()
    KEY = auto()


class SubType(Enum):
    HEALTH = auto()
    AGILITY = auto()
    STRENGTH = auto()
    KEY = auto()


class Item:
    def __init__(self):
        self._coords = Position(0, 0)

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, value):
        if not isinstance(value, Position):
            raise ValueError("Value must be of type Position")
        self._coords = value


class Treasure(Item):
    def __init__(self):
        super().__init__()
        self._type = ItemObjects.TREASURE
        self._price = 0

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        if value <= 0:
            raise ValueError("Value must be more than 0")
        self._price = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if not isinstance(value, ItemObjects):
            raise ValueError("Value must be of type ItemObjects")
        self._type = value


class ConsumableItem(Item):
    def __init__(self, name, type, subtype):
        super().__init__()
        self._name = name
        self._type = type
        self._subtype = subtype
        self._increase = MIN_INCREASE

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("Value must be of type str")
        self._name = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if not isinstance(value, ItemObjects):
            raise ValueError("Value must be of type ItemObjects")
        self._type = value

    @property
    def subtype(self):
        return self._subtype

    @subtype.setter
    def subtype(self, value):
        if not isinstance(value, SubType):
            raise ValueError("Value must be of type SubType")
        self._subtype = value

    @property
    def increase(self):
        return self._increase

    @increase.setter
    def increase(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        self._increase = value

    def generate_data(self, player):
        subtype = self.subtype
        match subtype:
            case SubType.HEALTH:
                self.increase = max(MIN_INCREASE, int(player.max_health * MAX_PERCENT_HEALTH_REGEN / 100))
            case SubType.AGILITY:
                self.increase = max(MIN_INCREASE, int(player.agility * MAX_PERCENT_AGILITY_INCREASE / 100))
            case SubType.STRENGTH:
                self.increase = max(MIN_INCREASE, int(player.strength * MAX_PERCENT_STRENGTH_INCREASE / 100))


class Scroll(ConsumableItem):
    names = [
        "Scroll of Shadowstep",
        "Parchment of Eternal Flame",
        "Manuscript of Forgotten Truths",
        "Scroll of Iron Will",
        "Vellum of the Void",
        "Scroll of Whispers",
        "Tome of the Lost King",
        "Scroll of Unseen Paths",
        "Parchment of Thunderous Roar",
    ]

    def __init__(self):
        super().__init__(name=choice(self.names),
                         type=ItemObjects.SCROLL,
                         subtype=choice(list(SubType)), )


class Elixir(ConsumableItem):
    names = [
        "Elixir of the Jade Serpent",
        "Potion of the Phantom's Breath",
        "Vial of Crimson Vitality",
        "Draught of the Frozen Star",
        "Elixir of the Shattered Mind",
        "Potion of the Wandering Soul",
        "Vial of Ember Essence",
        "Elixir of the Obsidian Veil",
        "Potion of the Howling Wind",
    ]

    def __init__(self):
        super().__init__(name=choice(self.names), type=ItemObjects.ELIXIR, subtype=choice(list(SubType)))
        self._duration = 1

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        if value <= 0:
            raise ValueError("Value must be more than 0")
        self._duration = value

    def generate_data(self, player):
        ConsumableItem.generate_data(self, player)
        self.duration = randint(MIN_ELIXIR_DURATION_SECONDS, MAX_ELIXIR_DURATION_SECONDS)


class Food(ConsumableItem):
    names = ["Ration of the Ironclad",
             "Crimson Berry Cluster",
             "Loaf of the Forgotten Baker",
             "Smoked Wyrm Jerky",
             "Golden Apple of Vitality",
             "Hardtack of the Endless March",
             "Spiced Venison Strips",
             "Honeyed Nectar Bread",
             "Dried Mushrooms of the Deep"]

    def __init__(self):
        super().__init__(
            name=choice(self.names),
            type=ItemObjects.FOOD,
            subtype=SubType.HEALTH,
        )

    def generate_data(self, player):
        max_regen = max(MIN_INCREASE, int(player.health * MAX_PERCENT_HEALTH_REGEN / 100))
        self.increase = randint(1, max_regen)


class Weapon(ConsumableItem):
    names = [
        "Blade of the Forgotten Dawn",
        "Obsidian Reaver",
        "Fang of the Shadow Wolf",
        "Ironclad Cleaver",
        "Crimson Talon",
        "Thunderstrike Maul",
        "Serpent's Kiss Dagger",
        "Voidrend Sword",
        "Ebonheart Spear",
    ]

    def __init__(self):
        super().__init__(
            name=choice(self.names),
            type=ItemObjects.WEAPON,
            subtype=SubType.STRENGTH)

    def generate_data(self, player):
        self.increase = randint(MIN_WEAPON_STRENGTH, MAX_WEAPON_STRENGTH)


class Key(ConsumableItem):
    def __init__(self, door_color):
        super().__init__(
            name=f"{door_color.name.lower()} key",
            type=ItemObjects.KEY,
            subtype=SubType.KEY)
        self._door_color = door_color

    @property
    def door_color(self):
        return self._door_color

    @door_color.setter
    def door_color(self, value):
        if not isinstance(value, DoorColor):
            raise ValueError("Value must be of type DoorColor")
        self._door_color = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if not isinstance(value, ItemObjects):
            raise ValueError("Value must be of type ItemObjects")
        self._type = value


def generate_key(door_color, coords):
    """Создать ключ определенного цвета"""
    key = Key(door_color)
    key.coords = coords
    return key


class ElixirBuff:
    def __init__(self, type, increase, end_time=1):
        self._type = type
        self._increase = increase
        self._end_time = end_time

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if not isinstance(value, SubType):
            raise ValueError("Value must be of type SubType")
        self._type = value

    @property
    def increase(self):
        return self._increase

    @increase.setter
    def increase(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        if value <= 0:
            raise ValueError("Value must be more than 0")
        self._increase = value

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        if value <= 0:
            raise ValueError("Value must be more than 0")
        self._end_time = value


def generate_item(player, coords):
    if randint(1, 100) <= 15:
        door_color_name = choice(["RED", "GREEN", "BLUE", "YELLOW"])
        door_color = DoorColor[door_color_name]
        key = Key(door_color)
        key.coords = coords
        return key

    item = choice(ConsumableItem.__subclasses__())()
    item.coords = coords
    item.generate_data(player)
    return item
