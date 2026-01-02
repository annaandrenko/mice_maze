"""
Pygame frontend for the console Labirint game.

Run:
    pip install pygame
    python -m labirint.main_pygame

Sprites:
    Put PNG files into assets/Sprites/ with these names:
        floor.png
        wall.png
        player.png
        exit.png
        (опційно) background.png / ui.png — якщо захочеш пізніше

You can start with any placeholder images; the code will fall back to simple coloured rectangles
if a sprite is missing.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

import pygame

from cells import Cell
from maze import Maze, generate_perfect_maze_cells
from player import Player
from Enemy import Enemy, spawn_enemies, move_enemies


ASSETS = Path("assets")
LEVELS = ASSETS / "Levels"
SPRITES_DIR = ASSETS / "Sprites"

DEFAULT_TILE = 32
FPS = 60

# Symbols used by your levels:
WALL_SYM = "#"
EXIT_SYM = "X"
CHEESE_SYM = "C"
CHEESE_COUNT = 10
ENEMY_SYM = "E"
ENEMY_COUNT = 5

PLAYER_MAX_HP = 3
ENEMY_DAMAGE = 1
HIT_COOLDOWN = 0.8  # сек — щоб не віднімало HP кожен кадр
ENEMY_STEP_DELAY = 0.35  # сек між кроками ворога

def _level_path(level: int) -> Path:
    return LEVELS / f"LVL{level}.txt"


def _safe_load_png(path: Path, size: int) -> Optional[pygame.Surface]:
    try:
        img = pygame.image.load(path.as_posix()).convert_alpha()
        if img.get_width() != size or img.get_height() != size:
            img = pygame.transform.smoothscale(img, (size, size))
        return img
    except Exception:
        return None


def load_sprites(tile: int) -> Dict[str, pygame.Surface]:
    sprites: Dict[str, pygame.Surface] = {}

    def load(name: str) -> Optional[pygame.Surface]:
        return _safe_load_png(SPRITES_DIR / name, tile)

    # Base tiles
    sprites["floor"] = load("floor.png") or None
    sprites["wall"] = load("wall.png") or None
    sprites["player"] = load("player.png") or None
    sprites["exit"] = load("exit.png") or None
    sprites["cheese"] = load("cheese.png") or None
    sprites["enemy"] = load("enemy.png") or None
    sprites["exit"] = load("exit.png") or None

    return {k: v for k, v in sprites.items() if v is not None}


def draw_fallback_rect(screen: pygame.Surface, rect: pygame.Rect, kind: str) -> None:
    colours = {
        "floor": (30, 30, 30),
        "wall": (90, 90, 90),
        "player": (230, 200, 40),
        "exit": (40, 200, 80),
        "cheese": (245, 220, 70),
        "enemy": (220, 60, 60),
    }
    c = colours.get(kind, (255, 255, 255))
    pygame.draw.rect(screen, c, rect)


def sprite_for_cell(cell: Cell) -> Tuple[str, Optional[str]]:
    sym = cell.symbol
    if sym == WALL_SYM:
        return "wall", None
    if sym == EXIT_SYM:
        return "exit", None
    if sym == CHEESE_SYM:
        return "cheese", None
    if sym == ENEMY_SYM:
        return "enemy", None
    return "floor", None


def render_world(
    screen: pygame.Surface,
    maze: Maze,
    player: Player,
    enemies: list,
    sprites: Dict[str, pygame.Surface],
    tile: int,
    font: pygame.font.Font,
) -> None:
    screen.fill((15, 15, 15))

    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.grid[y][x]
            kind, var = sprite_for_cell(cell)
            rect = pygame.Rect(x * tile, y * tile, tile, tile)

            # draw base (floor) first so transparent sprites look nice
            if "floor" in sprites:
                screen.blit(sprites["floor"], rect)
            else:
                draw_fallback_rect(screen, rect, "floor")

            # then overlay the actual cell if it's not floor
            if kind != "floor":
                key = kind if var is None else f"{kind}_{var}"
                if key in sprites:
                    screen.blit(sprites[key], rect)
                elif kind in sprites:
                    screen.blit(sprites[kind], rect)
                else:
                    draw_fallback_rect(screen, rect, key)

    # player on top
    prect = pygame.Rect(player.x * tile, player.y * tile, tile, tile)
    if "player" in sprites:
        screen.blit(sprites["player"], prect)
    else:
        draw_fallback_rect(screen, prect, "player")

    # --- Draw enemies ---
    for e in enemies:
        rect = pygame.Rect(e.x * tile, e.y * tile, tile, tile)

        # Якщо є спрайт ворога
        enemy_img = sprites.get("enemy")
        if enemy_img:
            screen.blit(enemy_img, rect)
        else:
            # fallback: червоний квадрат, щоб точно бачити
            pygame.draw.rect(screen, (200, 60, 60), rect)

    # HUD
    hud = f"{player.name} | HP: {getattr(player,'hp',3)} | Coins: {player.coins}"
    text = font.render(hud, True, (235, 235, 235))
    screen.blit(text, (8, maze.height * tile + 8))


def try_move(maze: Maze, player: Player, dx: int, dy: int) -> str:
    """
    Performs one movement step using the same rules as the console version.
    Returns a small status string (used for messages / debug).
    """
    nx, ny = player.x + dx, player.y + dy
    if not (0 <= nx < maze.width and 0 <= ny < maze.height):
        return "blocked"

    cell = maze.cell_at(nx, ny)
    sym = cell.symbol

    # wall
    if sym == WALL_SYM:
        return "wall"

    # exit
    if sym == EXIT_SYM:
        player.x, player.y = nx, ny
        return "exit"

    # cheese
    if sym == CHEESE_SYM:
        player.x, player.y = nx, ny
        player.coins += 1
        cell.symbol = " "
        return "cheese +1"

    if player.hp <= 0:
        message = "game over"
        message_timer = 2.0
        running = False

    # empty / other walkable
    player.x, player.y = nx, ny
    return "moved"



def spawn_cheese(maze: Maze, count: int, start_pos: tuple[int, int]) -> None:
    sx, sy = start_pos
    empties: list[tuple[int, int]] = []

    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.cell_at(x, y)
            if cell.walkable and cell.symbol == " " and (x, y) != (sx, sy):
                empties.append((x, y))

    exit_pos = maze.find_symbol(EXIT_SYM)
    if exit_pos in empties:
        empties.remove(exit_pos)

    random.shuffle(empties)
    for (x, y) in empties[:count]:
        maze.cell_at(x, y).symbol = CHEESE_SYM

def main() -> None:
    pygame.init()
    pygame.display.set_caption("Labirint (pygame)")
    clock = pygame.time.Clock()

    grid, (sx, sy) = generate_perfect_maze_cells(41, 21)
    maze = Maze(grid)

    player = Player(x=sx, y=sy, name="Player", coins=0)
    invuln = 0.0  # щоб не знімало хп 60 раз/сек
    ENEMY_COUNT = 4
    enemies = spawn_enemies(maze, ENEMY_COUNT, (sx, sy))

    ENEMY_DELAY = 0.25
    enemy_cd = 0.0

    spawn_cheese(maze, CHEESE_COUNT, (sx, sy))



    tile = DEFAULT_TILE
    hud_h = 40
    screen = pygame.display.set_mode((maze.width * tile, maze.height * tile + hud_h))
    font = pygame.font.SysFont(None, 22)

    sprites = load_sprites(tile)

    message = ""
    message_timer = 0.0

    running = True
    MOVE_DELAY = 0.12  # сек: меньше = быстрее шаги
    move_cooldown = 0.0
    enemy_cd = ENEMY_DELAY

    while running:
        dt = clock.tick(FPS) / 1000.0
        invuln = max(0.0, invuln - dt)
        move_cooldown = max(0.0, move_cooldown - dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,):
                    running = False

        enemy_cd -= dt
        if enemy_cd <= 0:
            move_enemies(maze, enemies)
            enemy_cd = ENEMY_DELAY

        # ===== Movement while holding keys =====
        keys = pygame.key.get_pressed()

        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1

        # делаем шаг только если кулдаун закончился
        if (dx or dy) and move_cooldown <= 0.0:
            message = try_move(maze, player, dx, dy)
            message_timer = 1.2
            move_cooldown = MOVE_DELAY
        # ======================================

        render_world(screen, maze, player, enemies, sprites, tile, font)

        # перевірка зіткнення з ворогами
        for e in enemies:
            if e.x == player.x and e.y == player.y and invuln <= 0:
                player.hp -= ENEMY_DAMAGE
                invuln = HIT_COOLDOWN
                message = f"hit! hp={player.hp}"
                message_timer = 1.2

        if player.hp <= 0:
            message = "GAME OVER"
            message_timer = 2.0
            running = False

        # simple message line
        if message_timer > 0:
            message_timer -= dt
            msg = font.render(message, True, (235, 235, 235))
            screen.blit(msg, (8, maze.height * tile + 8 + 18))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
