from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple

from entity import Entity
from maze import Maze

WALL_SYM = "#"
TURN_CHANCE = 0.22  # шанс “інколи повернути” (можеш змінити)


@dataclass
class Enemy(Entity):
    dx: int = 1
    dy: int = 0
    steps_left: int = 2
    max_steps: int = 2


def spawn_enemies(maze: Maze, count: int, avoid_xy: Tuple[int, int]) -> List[Enemy]:
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

        if random.random() < 0.5:
            dx, dy = random.choice([-1, 1]), 0
        else:
            dx, dy = 0, random.choice([-1, 1])

        max_steps = random.choice([2, 3])
        enemies.append(Enemy(x=x, y=y, dx=dx, dy=dy, steps_left=max_steps, max_steps=max_steps))

    return enemies


def move_enemies(maze: Maze, enemies: List[Enemy]) -> None:
    occupied = {(e.x, e.y) for e in enemies}
    reserved: set[tuple[int, int]] = set()

    order = enemies[:]
    random.shuffle(order)

    for e in order:
        # інколи змінює напрямок
        if random.random() < TURN_CHANCE:
            if e.dx != 0:
                e.dx, e.dy = 0, random.choice([-1, 1])
            else:
                e.dx, e.dy = random.choice([-1, 1]), 0
            e.steps_left = e.max_steps

        nx, ny = e.x + e.dx, e.y + e.dy

        blocked_by_wall = (
            not (0 <= nx < maze.width and 0 <= ny < maze.height)
            or maze.cell_at(nx, ny).symbol == WALL_SYM
        )

        blocked_by_enemy = (nx, ny) in occupied or (nx, ny) in reserved

        if blocked_by_wall or blocked_by_enemy:
            e.dx *= -1
            e.dy *= -1
            e.steps_left = e.max_steps
            reserved.add((e.x, e.y))
            continue

        occupied.remove((e.x, e.y))
        e.x, e.y = nx, ny
        reserved.add((e.x, e.y))
        occupied.add((e.x, e.y))

        e.steps_left -= 1
        if e.steps_left <= 0:
            e.dx *= -1
            e.dy *= -1
            e.steps_left = e.max_steps
