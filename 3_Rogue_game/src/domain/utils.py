from enum import Enum, auto


class Position:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        if value < 0:
            raise ValueError("Value must be >=0")
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        if not isinstance(value, int):
            raise ValueError("Value must be of type int")
        if value < 0:
            raise ValueError("Value must be >=0")
        self._y = value

    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y

    def __str__(self):
        return f"({self.x} {self.y})"


class Direction(Enum):
    STOP = auto()
    UP = auto()
    DOWN = auto()
    RIGHT = auto()
    LEFT = auto()
    DIAGONALLY_UP_RIGHT = auto()
    DIAGONALLY_UP_LEFT = auto()
    DIAGONALLY_DOWN_LEFT = auto()
    DIAGONALLY_DOWN_RIGHT = auto()


def directions_by_type(directions):
    directions_by_type = {
        "all": list(Direction),
        "simple": list(Direction)[1:4],
        "diagonals": list(Direction)[5:],
    }
    return directions_by_type[directions]


class DoorColor(Enum):
    NONE = auto()
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    YELLOW = auto()


class Edge:
    def __init__(self, u, v):
        self.u = u  # ///< Первая вершина ребра
        self.v = v  # ///< Вторая вершина ребра


def make_sets(parent: list, rank: list, size: int):
    for i in range(size):
        parent[i] = i
        rank[i] = 0


def find_set(v: int, parent: list):
    if v == parent[v]:
        return v
    return find_set(parent[v], parent)


def union_sets(v: int, u: int, parent: list, rank: list):
    v = find_set(v, parent)
    u = find_set(u, parent)

    if u != v:
        if rank[u] >= rank[v]:
            parent[v] = u
        else:
            parent[u] = v

        if rank[u] == rank[v]:
            rank[u] += 1


def get_bresenham_line_coords(x0, y0, x1, y1):
    coords = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    d = dx - dy

    while True:
        coords.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        d2 = 2 * d
        if d2 > -dy:
            d -= dy
            x0 += sx
        if d2 < dx:
            d += dx
            y0 += sy
    return coords
