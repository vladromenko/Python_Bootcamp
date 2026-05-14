from consts import MAX_ITEM_COUNT_IN_BACKPACK
from domain.items import ItemObjects


class BackpackObserver:
    def backpack_is_full(self, item):
        pass


class Backpack:
    def __init__(self):
        self.scrolls = []
        self.elixirs = []
        self.treasures = []
        self.foods = []
        self.weapons = []
        self._observers = []
        self.keys = {}

    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def get_items_by_type(self, item_type):
        match item_type:
            case ItemObjects.SCROLL:
                return self.scrolls
            case ItemObjects.ELIXIR:
                return self.elixirs
            case ItemObjects.FOOD:
                return self.foods
            case ItemObjects.WEAPON:
                return self.weapons
            case ItemObjects.TREASURE:
                return self.treasures
            case ItemObjects.KEY:
                return list(self.keys.values())
        return []

    def count_items(self, item_type):
        items_by_type = self.get_items_by_type(item_type)
        return len(items_by_type)

    def _check_backpack_capacity_for_items(self, item):
        if item.type == ItemObjects.TREASURE:
            return True

        # Особый случай для ключей - максимум один ключ каждого цвета
        if item.type == ItemObjects.KEY:
            if item.door_color in self.keys:
                return False  # Уже есть ключ этого цвета
            return True

        items_by_type = self.get_items_by_type(item.type)
        if len(items_by_type) >= MAX_ITEM_COUNT_IN_BACKPACK:
            return False
        return True

    def grab_item_in_backpack(self, item):
        if not self._check_backpack_capacity_for_items(item):
            self.__notify_backpack_is_full(item)
            return False

        if item.type == ItemObjects.KEY:
            # Проверяем, нет ли уже ключа этого цвета
            if item.door_color in self.keys:
                return False
            self.keys[item.door_color] = item
            return True

        items_by_type = self.get_items_by_type(item.type)
        items_by_type.append(item)
        return True

    def remove_item_from_backpack(self, type, index):

        if type == ItemObjects.KEY:
            # Для ключей нужно найти по индексу
            keys_list = list(self.keys.values())
            if 0 <= index < len(keys_list):
                key = keys_list[index]
                del self.keys[key.door_color]
                return key
            return None

        items_by_type = self.get_items_by_type(type)
        return items_by_type.pop(index)

    def __notify_backpack_is_full(self, item):
        for i in self._observers:
            i.backpack_is_full(item)

    def has_key_for_color(self, door_color):
        return door_color in self.keys

    def use_key(self, door_color):
        return self.has_key_for_color(door_color)
