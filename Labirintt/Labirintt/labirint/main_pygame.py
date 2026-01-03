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
from enum import Enum, auto

class GameState(Enum):
    MENU = auto()
    GAME = auto()


ASSETS = Path("assets")
MENU_BG = ASSETS / "Menu" / "background.jpg"
LEVELS = ASSETS / "Levels"
SPRITES_DIR = ASSETS / "Sprites"

DEFAULT_TILE = 24
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
HIT_COOLDOWN = 0.8
ENEMY_STEP_DELAY = 0.35
HEAL_SYM = "H"
HEAL_COUNT = 3

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
    sprites["heal"] = load("heal.png") or None
    sprites["heart"] = load("heart.png") or None

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
    if sym == HEAL_SYM:
        return "heal", None
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

    # --- HUD ---
    hud_y = maze.height * tile
    x = 12

    name_surf = font.render(player.name, True, (235, 235, 235))
    screen.blit(name_surf, (x, hud_y + 8))
    x += name_surf.get_width() + 30

    heart_img = sprites.get("heart")
    if heart_img:
        # центруємо сердечка по висоті HUD
        y_heart = hud_y + 8  # можеш змінити на 10/6 якщо хочеш вище/нижче
        gap = 4
        for i in range(player.hp):
            screen.blit(heart_img, (x + i * (heart_img.get_width() + gap), y_heart))
        x += player.hp * (heart_img.get_width() + gap) + 30
    else:
        hp_surf = font.render(f"HP: {player.hp}", True, (235, 235, 235))
        screen.blit(hp_surf, (x, hud_y + 8))
        x += hp_surf.get_width() + 30

    # --- Coins icon + text ---
    coin_img = sprites.get("coin") or sprites.get("cheese")  # якщо coin нема — беремо cheese
    icon_size = 18
    gap = 6

    if coin_img:
        coin_icon = pygame.transform.smoothscale(coin_img, (icon_size, icon_size))
        screen.blit(coin_icon, (x, hud_y + 8))
        x += icon_size + gap

    coins_surf = font.render(f"Coins: {player.coins}", True, (235, 235, 235))
    screen.blit(coins_surf, (x, hud_y + 8))
    x += coins_surf.get_width() + 20


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

    # heal item
    if sym == HEAL_SYM:
        player.x, player.y = nx, ny

        player.hp = min(PLAYER_MAX_HP, player.hp + 1)

        cell.symbol = " "
        return "heal +1"

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

def spawn_heal_items(maze: Maze, count: int, start_pos: tuple[int, int]) -> None:
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
        maze.cell_at(x, y).symbol = HEAL_SYM


def run_main_menu(screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font,  bg: pygame.Surface | None,) -> tuple[bool, str]:
        """
        Повертає (start_game, player_name).
        start_game=False => вихід з програми.
        """
        name = ""
        active = True  # поле вводу активне завжди (поки так простіше)

        while True:
            dt = clock.tick(60) / 1000.0


            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False, ""

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False, ""

                    if event.key == pygame.K_RETURN:
                        final_name = name.strip() or "Player"
                        return True, final_name

                    if event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    else:
                        # вводимо лише нормальні символи
                        if len(event.unicode) == 1 and event.unicode.isprintable():
                            if len(name) < 16:
                                name += event.unicode

            # ---- render menu ----
            if bg:
                screen.blit(bg, (0, 0))
            else:
                screen.fill((10, 10, 12))

            title = font.render("=MICE MAZE=", True, ((180, 235, 180)))
            screen.blit(title, (40, 40))

            # ---- UI PANEL ----
            panel = pygame.Surface((380, 300), pygame.SRCALPHA)
            panel.fill((10, 40, 20, 130))
            screen.blit(panel, (20, 20))

            welcome1 = font.render("Привіт, мишеня!", True, (235, 235, 235))
            welcome2 = font.render("Збери сир, уникай ворогів", True, (200, 200, 200))
            welcome3 = font.render("і знайди вихід з лабіринту", True, (200, 200, 200))
            screen.blit(welcome1, (40, 120))
            screen.blit(welcome2, (40, 145))
            screen.blit(welcome3, (40, 170))


            label = font.render("Твоє ім'я...", True, (235, 235, 235))
            screen.blit(label, (40, 215))

            # поле вводу
            box = pygame.Rect(40, 240, 300, 36)
            pygame.draw.rect(screen, (40, 40, 45), box, border_radius=6)
            pygame.draw.rect(screen, (110, 110, 120), box, width=2, border_radius=6)

            text = font.render(name if name else "?...", True, (235, 235, 235) if name else (150, 150, 150))
            screen.blit(text, (box.x + 10, box.y + 8))

            hint = font.render("Натисни Enter, щоб почати гру", True, (140, 200, 140))
            screen.blit(hint, (40, 285))

            pygame.display.flip()

def main() -> None:
    import os
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    pygame.init()
    pygame.display.set_caption("Labirint (pygame)")
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((640, 360))
    font = pygame.font.SysFont(None, 32)

    menu_bg = None
    if MENU_BG.exists():
        menu_bg = pygame.image.load(MENU_BG.as_posix()).convert()
        menu_bg = pygame.transform.scale(menu_bg, (640, 360))

    # --- MENU ---
    start, player_name = run_main_menu(screen, clock, font, menu_bg)
    if not start:
        pygame.quit()
        sys.exit(0)

    pygame.display.set_caption("Labirint (pygame)")

    grid, (sx, sy) = generate_perfect_maze_cells(41, 21)
    maze = Maze(grid)

    player = Player(x=sx, y=sy, name=player_name, coins=0)
    player.hp = PLAYER_MAX_HP

    invuln = 0.0  # щоб не знімало хп 60 раз/сек
    ENEMY_COUNT = 4
    enemies = spawn_enemies(maze, ENEMY_COUNT, (sx, sy))

    ENEMY_DELAY = 0.25
    enemy_cd = 0.0

    spawn_cheese(maze, CHEESE_COUNT, (sx, sy))
    spawn_heal_items(maze, HEAL_COUNT, (sx, sy))

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
