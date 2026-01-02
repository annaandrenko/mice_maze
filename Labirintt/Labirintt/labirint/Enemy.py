from __future__ import annotations
from dataclasses import dataclass
import random
from typing import List, Tuple

from maze import Maze
WALL_SYM = "#"


@dataclass
class Enemy:
    x: int
    y: int
    dx: int
    dy: int
    steps_left: int
    max_steps: int


def spawn_enemies(maze: Maze, count: int, avoid_xy: Tuple[int, int]) -> List[Enemy]:
    """Спавнить ворогів на порожніх клітинках, не біля старту."""
    enemies: List[Enemy] = []
    tries = 0

    while len(enemies) < count and tries < 5000:
        tries += 1
        p = maze.random_empty_cell()
        if not p:
            break
        x, y = p

        ax, ay = avoid_xy
        if abs(x - ax) + abs(y - ay) <= 2:
            continue

        if any(e.x == x and e.y == y for e in enemies):
            continue

        # рух: або горизонтально, або вертикально
        if random.random() < 0.5:
            dx, dy = random.choice([-1, 1]), 0
        else:
            dx, dy = 0, random.choice([-1, 1])

        max_steps = random.choice([2, 3])
        enemies.append(Enemy(x=x, y=y, dx=dx, dy=dy, steps_left=max_steps, max_steps=max_steps))

    return enemies


def move_enemies(maze: Maze, enemies: List[Enemy]) -> None:
    """Один крок: вороги ходять туди-сюди, відбиваються від стін/меж."""
    for e in enemies:
        nx, ny = e.x + e.dx, e.y + e.dy

        # стіна або межа — розвернутись
        if not (0 <= nx < maze.width and 0 <= ny < maze.height) or maze.cell_at(nx, ny).symbol == WALL_SYM:
            e.dx *= -1
            e.dy *= -1
            e.steps_left = e.max_steps
            continue

        e.x, e.y = nx, ny
        e.steps_left -= 1

        if e.steps_left <= 0:
            e.dx *= -1
            e.dy *= -1
            e.steps_left = e.max_steps
