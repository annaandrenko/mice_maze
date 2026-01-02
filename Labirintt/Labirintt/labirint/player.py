from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from cells import Cell

@dataclass
class Item:
    name: str
    price: int

@dataclass
class Player:
    x: int
    y: int
    name: str = "Player"
    coins: int = 0
    lives: int = 3
    hp: int = 5
    inventory: List[Item] = field(default_factory=list)

    def add_item(self, item: Item):
        self.inventory.append(item)

    def use_bomb(self, grid: list[list[Cell]]) -> bool:
        bomb: Optional[Item] = next((it for it in self.inventory if it.name == "Бомбочка"), None)
        if not bomb:
            return False

        h = len(grid)
        w = len(grid[0]) if h else 0
        # Спрощення: лишаємо тільки стіни як руйнівні.
        destroyable = {"#"}
        for yy in range(self.y - 1, self.y + 2):
            for xx in range(self.x - 1, self.x + 2):
                if 0 <= yy < h and 0 <= xx < w:
                    if grid[yy][xx].symbol in destroyable:
                        grid[yy][xx] = Cell()
        self.inventory.remove(bomb)
        return True
