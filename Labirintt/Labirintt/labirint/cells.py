from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from ansi import color

class CellType(Enum):
    EMPTY = auto()
    WALL = auto()
    EXIT = auto()

@dataclass
class Cell:
    symbol: str = " "
    walkable: bool = True
    cell_type: CellType = CellType.EMPTY

    def render(self) -> str:
        s = self.symbol
        if s == "#":
            return color(s, "bright_black")
        if s == "X":
            return color(s, "white")
        if s == "●":
            return color(s, "yellow")
        return s

class WallCell(Cell):
    def __init__(self):
        super().__init__(symbol="#", walkable=False, cell_type=CellType.WALL)

class ExitCell(Cell):
    def __init__(self):
        super().__init__(symbol="X", walkable=True, cell_type=CellType.EXIT)
