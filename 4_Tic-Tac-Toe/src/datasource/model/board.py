from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Board:
    cells: List[List[int]]
