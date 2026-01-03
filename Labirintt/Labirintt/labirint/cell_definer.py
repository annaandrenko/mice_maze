from __future__ import annotations

from typing import Callable, Dict

from cells import Cell, WallCell, ExitCell

_SIMPLE: Dict[str, Callable[[], Cell]] = {
    " ": lambda: Cell(),
    "#": lambda: WallCell(),
    "X": lambda: ExitCell(),
}

def cell_from_char(ch: str) -> Cell:
    if ch == "#":
        return Cell(symbol="#", walkable=False)

    if ch == " ":
        return Cell(symbol=" ", walkable=True)

    if ch == "X":
        return Cell(symbol="X", walkable=True)

    return Cell(symbol=" ", walkable=True)

