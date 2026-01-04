from __future__ import annotations

import json
from datetime import datetime

import random
from pathlib import Path
from typing import Dict, Tuple, Optional

import pygame

from cells import Cell
from maze import Maze, generate_perfect_maze_cells
from player import Player
from Enemy import spawn_enemies, move_enemies
from enum import Enum, auto
from maze import load_map
from Enemy import Enemy

class GameState(Enum):
    MENU = auto()
    GAME = auto()


ASSETS = Path("assets")
MENU_BG = ASSETS / "Menu" / "background.jpg"
LEVELS = ASSETS / "Levels"
SPRITES_DIR = ASSETS / "Sprites"

DEFAULT_TILE = 24
FPS = 60
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
DIFFICULTIES = {
    "EASY": {
        "size": (31, 15),
        "enemies": 2,
        "cheese": 8,
        "heal": 5,
        "enemy_delay": 0.45,
        "move_delay": 0.10,
    },
    "NORMAL": {
        "size": (37, 19),
        "enemies": 3,
        "cheese": 10,
        "heal": 3,
        "enemy_delay": 0.30,
        "move_delay": 0.12,
    },
    "HARD": {
        "size": (41, 21),
        "enemies": 4,
        "cheese": 13,
        "heal": 2,
        "enemy_delay": 0.22,
        "move_delay": 0.14,
    },
}
CHEESE_MOVE_DELAY = 1.2
CHEESE_MOVE_CHANCE = 0.6
MUSIC_VOLUME = 0.4
MUSIC_MUTED = False
MUSIC_STOPPED = False
SAVES_DIR = Path("saves")
SAVE_FILE = SAVES_DIR / "players.json"





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
            if "floor" in sprites:
                screen.blit(sprites["floor"], rect)
            else:
                draw_fallback_rect(screen, rect, "floor")
            if kind != "floor":
                key = kind if var is None else f"{kind}_{var}"
                if key in sprites:
                    screen.blit(sprites[key], rect)
                elif kind in sprites:
                    screen.blit(sprites[kind], rect)
                else:
                    draw_fallback_rect(screen, rect, key)


    prect = pygame.Rect(player.x * tile, player.y * tile, tile, tile)
    if "player" in sprites:
        screen.blit(sprites["player"], prect)
    else:
        draw_fallback_rect(screen, prect, "player")

    for e in enemies:
        rect = pygame.Rect(e.x * tile, e.y * tile, tile, tile)

        enemy_img = sprites.get("enemy")
        if enemy_img:
            screen.blit(enemy_img, rect)
        else:
            pygame.draw.rect(screen, (200, 60, 60), rect)

    # --- HUD ---
    hud_y = maze.height * tile
    x = 12

    name_surf = font.render(player.name, True, (235, 235, 235))
    screen.blit(name_surf, (x, hud_y + 8))
    x += name_surf.get_width() + 30

    heart_img = sprites.get("heart")
    if heart_img:
        y_heart = hud_y + 8
        gap = 4
        for i in range(player.hp):
            screen.blit(heart_img, (x + i * (heart_img.get_width() + gap), y_heart))
        x += player.hp * (heart_img.get_width() + gap) + 30
    else:
        hp_surf = font.render(f"HP: {player.hp}", True, (235, 235, 235))
        screen.blit(hp_surf, (x, hud_y + 8))
        x += hp_surf.get_width() + 30

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

def move_cheese(maze: Maze, player: Player, enemies: list) -> None:
    cheeses: list[tuple[int, int]] = []
    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.cell_at(x, y)
            if cell.symbol == CHEESE_SYM:
                cheeses.append((x, y))

    enemy_positions = {(e.x, e.y) for e in enemies}
    px, py = player.x, player.y

    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    random.shuffle(cheeses)

    for (x, y) in cheeses:
        if random.random() > CHEESE_MOVE_CHANCE:
            continue

        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < maze.width and 0 <= ny < maze.height):
                continue

            target = maze.cell_at(nx, ny)
            if target.walkable and target.symbol == " " and (nx, ny) != (px, py) and (nx, ny) not in enemy_positions:
                maze.cell_at(x, y).symbol = " "
                target.symbol = CHEESE_SYM
                break


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


def run_main_menu(screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font,  bg: pygame.Surface | None,) -> tuple[bool, str, str]:

        name = ""
        name_active = False
        difficulty = "HARD"
        box = pygame.Rect(40, 240, 300, 36)
        cursor_timer = 0.0
        cursor_visible = True
        total_coins = load_total_coins()
        small_font = pygame.font.SysFont(None, 20)

        while True:
            dt = clock.tick(60) / 1000.0
            cursor_timer += dt
            if cursor_timer >= 0.5:  # миготіння кожні 0.5 сек
                cursor_timer = 0.0
                cursor_visible = not cursor_visible

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    name_active = box.collidepoint(event.pos)
                    if name_active:
                        cursor_visible = True
                        cursor_timer = 0.0

                if event.type == pygame.QUIT:
                    return False, "", "HARD"
                global MUSIC_VOLUME, MUSIC_MUTED, MUSIC_STOPPED
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False, "", "HARD"

                    if event.key == pygame.K_RETURN:
                        final_name = name.strip() or "Player"
                        return True, final_name, difficulty

                    if event.key == pygame.K_BACKSPACE:
                        name = name[:-1]

                    if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        MUSIC_VOLUME = max(0.0, MUSIC_VOLUME - 0.05)
                        if not MUSIC_MUTED:
                            pygame.mixer.music.set_volume(MUSIC_VOLUME)

                    if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                        MUSIC_VOLUME = min(1.0, MUSIC_VOLUME + 0.05)
                        if not MUSIC_MUTED:
                            pygame.mixer.music.set_volume(MUSIC_VOLUME)

                    if event.key == pygame.K_m:
                        MUSIC_MUTED = not MUSIC_MUTED
                        pygame.mixer.music.set_volume(0.0 if MUSIC_MUTED else MUSIC_VOLUME)

                    if event.key == pygame.K_s:
                        # S = stop / start
                        if MUSIC_STOPPED:
                            pygame.mixer.music.play(-1)
                            pygame.mixer.music.set_volume(0.0 if MUSIC_MUTED else MUSIC_VOLUME)
                            MUSIC_STOPPED = False
                        else:
                            pygame.mixer.music.stop()
                            MUSIC_STOPPED = True

                    if event.key == pygame.K_1:
                        difficulty = "EASY"
                    elif event.key == pygame.K_2:
                        difficulty = "NORMAL"
                    elif event.key == pygame.K_3:
                        difficulty = "HARD"

                    if event.key == pygame.K_e:#запуск редактора
                        return True, "__EDITOR__", difficulty
                    if event.key == pygame.K_c:#запуск кастомногог рівня
                        return True, "__CUSTOM__", difficulty



                    elif name_active:
                        if event.key == pygame.K_BACKSPACE:
                            name = name[:-1]
                        elif len(event.unicode) == 1 and event.unicode.isprintable():
                            if len(name) < 16:
                                name += event.unicode

                    elif len(event.unicode) == 1 and event.unicode.isprintable():
                        if len(name) < 16:
                            name += event.unicode

                    else:
                        if len(event.unicode) == 1 and event.unicode.isprintable():
                            if len(name) < 16:
                                name += event.unicode

            if bg:
                screen.blit(bg, (0, 0))
            else:
                screen.fill((10, 10, 12))

            title = font.render("=MICE MAZE=", True, ((180, 235, 180)))
            screen.blit(title, (40, 40))

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

            display_name = name

            if name_active and cursor_visible:
                display_name = (name if name else "") + "|"

            text = font.render(display_name if display_name else "?...", True,
                               (235, 235, 235) if name else (150, 150, 150))
            screen.blit(text, (box.x + 10, box.y + 8))

            screen.blit(text, (box.x + 10, box.y + 8))

            diff_text = font.render(f"Складність: {difficulty} (1–3)", True, (140, 200, 140))
            screen.blit(diff_text, (40, 310))



            hint = font.render("Натисни Enter, щоб почати гру", True, (140, 200, 140))
            screen.blit(hint, (40, 285))


            pygame.display.flip()

def run_pause_menu(screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font) -> str:
    bg = screen.copy()
    selected = 0
    options = ["Продовжити", "В головне меню"]

    w, h = screen.get_size()


    panel = pygame.Rect(0, 0, 360, 200)
    panel.center = (w // 2, h // 2)

    hint_gen = hint_generator()
    current_hint = next(hint_gen)
    hint_timer = 0.0


    while True:
        dt = clock.tick(60) / 1000.0
        hint_timer -= dt
        if hint_timer <= 0:
            try:
                current_hint = next(hint_gen)
            except StopIteration:
                hint_gen = hint_generator()
                current_hint = next(hint_gen)
            hint_timer = 4.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    return "resume"

                if event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(options)

                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(options)

                global MUSIC_VOLUME, MUSIC_MUTED, MUSIC_STOPPED

                # +/- гучність
                if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    MUSIC_VOLUME = max(0.0, MUSIC_VOLUME - 0.05)
                    if not MUSIC_MUTED and not MUSIC_STOPPED:
                        pygame.mixer.music.set_volume(MUSIC_VOLUME)

                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    MUSIC_VOLUME = min(1.0, MUSIC_VOLUME + 0.05)
                    if not MUSIC_MUTED and not MUSIC_STOPPED:
                        pygame.mixer.music.set_volume(MUSIC_VOLUME)

                # M mute
                elif event.key == pygame.K_m:
                    MUSIC_MUTED = not MUSIC_MUTED
                    if not MUSIC_STOPPED:
                        pygame.mixer.music.set_volume(0.0 if MUSIC_MUTED else MUSIC_VOLUME)

                # S stop/start
                elif event.key == pygame.K_s:
                    if MUSIC_STOPPED:
                        pygame.mixer.music.play(-1)
                        pygame.mixer.music.set_volume(0.0 if MUSIC_MUTED else MUSIC_VOLUME)
                        MUSIC_STOPPED = False
                    else:
                        pygame.mixer.music.stop()
                        MUSIC_STOPPED = True

                elif event.key == pygame.K_o:
                    if MUSIC_STOPPED:
                        pygame.mixer.music.play(-1)
                        MUSIC_STOPPED = False

                    MUSIC_MUTED = False
                    pygame.mixer.music.set_volume(MUSIC_VOLUME)

                if event.key == pygame.K_RETURN:
                    return "resume" if selected == 0 else "menu"

        screen.blit(bg, (0, 0))

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        w, h = screen.get_size()
        panel = pygame.Rect(0, 0, 360, 200)
        panel.center = (w // 2, h // 2)

        panel_surf = pygame.Surface(panel.size, pygame.SRCALPHA)
        panel_surf.fill((10, 40, 20, 180))  # темно-зелений, прозорий
        screen.blit(panel_surf, panel.topleft)

        pygame.draw.rect(screen, (140, 200, 140), panel, width=2, border_radius=10)

        title = font.render("ПАУЗА", True, (180, 235, 180))
        screen.blit(title, (panel.x + 20, panel.y + 18))

        for i, text in enumerate(options):
            y = panel.y + 70 + i * 36

            if i == selected:
                highlight = pygame.Rect(panel.x + 15, y - 4, panel.width - 30, 32)
                pygame.draw.rect(screen, (20, 60, 30), highlight, border_radius=6)

                color = (210, 245, 210)  # світлий текст на темному
            else:
                color = (230, 230, 230)  # звичайний світлий текст

            line = font.render(text, True, color)
            screen.blit(line, (panel.x + 30, y))

        hint = font.render("Enter - вибрати", True, (160, 200, 160))
        screen.blit(hint, (panel.x + 20, panel.y + 150))
        vol = int(MUSIC_VOLUME * 100)
        state = "OFF" if MUSIC_STOPPED else ("MUTED" if MUSIC_MUTED else "ON")
        hint = font.render(f"Sound: {state} | Volume: {vol}%   (+/-)  M-mute  S-stop", True, (220, 220, 220))
        screen.blit(hint, (20, panel.y + panel.height + 10))

        hint_surface = font.render(current_hint, True, (160, 210, 160))
        screen.blit(
            hint_surface,
            (panel.x + 20, panel.y + panel.height - 30)
        )

        pygame.display.flip()

def hint_generator():
    hints = [
        "Збери весь сир",
        "Уникай котів!",
        "Натисни ESC для паузи"
    ]
    for h in hints:
        yield h

def run_end_menu(screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font,
                 is_win: bool, player: Player) -> str:

    if is_win:
        bg = pygame.image.load("assets/Menu/win.png").convert()
    else:
        bg = pygame.image.load("assets/Menu/lose.png").convert()

    bg = pygame.transform.scale(bg, screen.get_size())

    w, h = screen.get_size()

    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))

    screen.blit(bg, (0, 0))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(0, 0, 420, 240)
    panel.center = (w // 2, h // 2)

    options = ["В головне меню", "Вийти з гри"]
    selected = 0

    title = "ПЕРЕМОГА!" if is_win else "ПОРАЗКА"
    subtitle = "Ти дійшов до виходу!" if is_win else "У тебе закінчились HP."
    hint = "Enter підтвердити   Esc = меню"


    while True:
        title_font = pygame.font.SysFont(None, 54)
        sub_font = pygame.font.SysFont(None, 26)
        btn_font = pygame.font.SysFont(None, 34)

        while True:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

                    elif event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(options)

                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(options)

                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        return "menu" if selected == 0 else "quit"

            # ==== RENDER ====
            w, h = screen.get_size()

            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))  # затемнення

            panel_surf = pygame.Surface(panel.size, pygame.SRCALPHA)
            panel_surf.fill((30, 30, 40, 180))  # 180 = напівпрозорий

            # фон + затемнення + панель
            screen.blit(bg, (0, 0))
            screen.blit(overlay, (0, 0))
            screen.blit(panel_surf, panel.topleft)

            # рамка
            border_color = (80, 200, 120) if is_win else (220, 80, 80)
            pygame.draw.rect(screen, border_color, panel, width=3, border_radius=16)

            # тексти
            t_surf = title_font.render(title, True, (245, 245, 245))
            s_surf = sub_font.render(subtitle, True, (210, 210, 210))
            screen.blit(t_surf, (panel.centerx - t_surf.get_width() // 2, panel.y + 22))
            screen.blit(s_surf, (panel.centerx - s_surf.get_width() // 2, panel.y + 80))

            stats = f"Гравець: {player.name}   |   Coins: {player.coins}   |   HP: {player.hp}"
            st_surf = sub_font.render(stats, True, (200, 200, 220))
            screen.blit(st_surf, (panel.centerx - st_surf.get_width() // 2, panel.y + 118))

            # кнопки
            y0 = panel.y + 155
            for i, text in enumerate(options):
                col = (255, 255, 255) if i == selected else (170, 170, 170)
                prefix = " " if i == selected else "   "
                b_surf = btn_font.render(prefix + text, True, col)
                screen.blit(b_surf, (panel.x + 40, y0 + i * 38))

            # підказка
            h_surf = sub_font.render(hint, True, (170, 170, 170))
            screen.blit(h_surf, (panel.centerx - h_surf.get_width() // 2, panel.bottom + 18))

            pygame.display.flip()

def _load_all_players() -> dict:
    """Return dict with structure: {'players': {name: {'coins': int, 'updated_at': str}}, 'last_player': str}"""
    try:
        if not SAVE_FILE.exists():
            return {"players": {}, "last_player": ""}

        data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"players": {}, "last_player": ""}

        data.setdefault("players", {})
        data.setdefault("last_player", "")
        return data
    except Exception:
        return {"players": {}, "last_player": ""}


def _save_all_players(data: dict) -> None:
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_player_coins(player_name: str) -> int:
    data = _load_all_players()
    p = data["players"].get(player_name)
    if isinstance(p, dict) and isinstance(p.get("coins"), int):
        return p["coins"]
    return 0

def load_total_coins() -> int:
    data = _load_all_players()
    total = 0

    for p in data.get("players", {}).values():
        if isinstance(p, dict):
            total += int(p.get("coins", 0))

    return total



def save_player_progress(player_name: str, coins: int) -> None:
    data = _load_all_players()
    data["players"].setdefault(player_name, {})
    data["players"][player_name]["coins"] = int(coins)
    data["players"][player_name]["updated_at"] = datetime.now().isoformat(timespec="seconds")
    data["last_player"] = player_name
    _save_all_players(data)



def main() -> None:
    import os
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    pygame.init()
    pygame.mixer.init()

    try:
        pygame.mixer.music.load("assets/Sounds/sound.oog")
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        pygame.mixer.music.play(-1)
    except pygame.error as e:
        print("Помилка завантаження музики:", e)
        MUSIC_STOPPED = True

    pygame.display.set_caption("Labirint (pygame)")
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((640, 360))
    font = pygame.font.SysFont(None, 32)
    total_coins = load_total_coins()

    pygame.mixer.music.load("assets/Sounds/sound.mp3")
    pygame.mixer.music.set_volume(0.4)  # 0.0 – 1.0
    pygame.mixer.music.play(-1)  # -1 = нескінченний циклввввц

    menu_bg = None
    if MENU_BG.exists():
        menu_bg = pygame.image.load(MENU_BG.as_posix()).convert()
        menu_bg = pygame.transform.scale(menu_bg, (640, 360))

    start, player_name, difficulty = run_main_menu(screen, clock, font, menu_bg)
    if player_name == "__EDITOR__":
        from editor import run_editor
        run_editor(screen, clock, font)
        return "menu"

    if not start:
        pygame.quit()
        return "quit"



    pygame.display.set_caption("Labirint (pygame)")


    cfg = DIFFICULTIES[difficulty]
    PLAYER_START_SYM = "S"
    is_custom = (player_name == "__CUSTOM__")
    if player_name == "__CUSTOM__":
        level_path = (LEVELS / "LVL_EDITOR.txt").as_posix()
        grid = load_map(level_path)
        maze = Maze(grid)

        pos = maze.find_symbol(PLAYER_START_SYM)
        if pos:
            sx, sy = pos
            maze.cell_at(sx, sy).symbol = " "
        else:
            sx, sy = 1, 1

        enemies = []
        for y in range(maze.height):
            for x in range(maze.width):
                if maze.cell_at(x, y).symbol == ENEMY_SYM:
                    enemies.append(Enemy(x=x, y=y))
                    maze.cell_at(x, y).symbol = " "
    else:
        grid, (sx, sy) = generate_perfect_maze_cells(*cfg["size"])
        maze = Maze(grid)
        enemies = spawn_enemies(maze, cfg["enemies"], (sx, sy))
        spawn_cheese(maze, cfg["cheese"], (sx, sy))
        spawn_heal_items(maze, cfg["heal"], (sx, sy))

    saved_coins = load_player_coins(player_name)
    player = Player(x=sx, y=sy, name=player_name, coins=saved_coins)
    player.hp = PLAYER_MAX_HP

    ENEMY_DELAY = cfg["enemy_delay"]
    MOVE_DELAY = cfg["move_delay"]
    invuln = 0.0

    if not is_custom:
        enemies = spawn_enemies(maze, cfg["enemies"], (sx, sy))
        spawn_cheese(maze, cfg["cheese"], (sx, sy))
        spawn_heal_items(maze, cfg["heal"], (sx, sy))

    tile = DEFAULT_TILE
    hud_h = 40
    screen = pygame.display.set_mode((maze.width * tile, maze.height * tile + hud_h))
    font = pygame.font.SysFont(None, 22)

    sprites = load_sprites(tile)

    message = ""
    message_timer = 0.0

    running = True
    move_cooldown = 0.0
    enemy_cd = ENEMY_DELAY
    end_state = None
    back_to_menu = False
    cheese_cd = CHEESE_MOVE_DELAY

    while running:
        dt = clock.tick(FPS) / 1000.0
        cheese_cd -= dt
        if cheese_cd <= 0:
            move_cheese(maze, player, enemies)
            cheese_cd = CHEESE_MOVE_DELAY
        invuln = max(0.0, invuln - dt)
        move_cooldown = max(0.0, move_cooldown - dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not MUSIC_STOPPED:
                            pygame.mixer.music.pause()

                        action = run_pause_menu(screen, clock, font)

                        if action == "resume":
                            if not MUSIC_STOPPED:
                                pygame.mixer.music.unpause()

                        elif action == "menu":
                            running = False
                            back_to_menu = True

                        elif action == "quit":
                            running = False
                            back_to_menu = False

                if event.key == pygame.K_F1:
                    player.hp = min(PLAYER_MAX_HP, player.hp + 1)
                    message = f"CHEAT: +1 HP ({player.hp}/{PLAYER_MAX_HP})"
                    message_timer = 1.2

                if event.key == pygame.K_F2:
                    enemies.clear()
                    message = "CHEAT: all enemies removed"
                    message_timer = 1.2

        enemy_cd -= dt
        if enemy_cd <= 0:
            move_enemies(maze, enemies)
            enemy_cd = ENEMY_DELAY

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

        if (dx or dy) and move_cooldown <= 0.0:
            message = try_move(maze, player, dx, dy)
            message_timer = 1.2
            move_cooldown = MOVE_DELAY

            if message == "exit":
                end_state = "win"
                running = False

        render_world(screen, maze, player, enemies, sprites, tile, font)

        for e in enemies:
            if e.x == player.x and e.y == player.y and invuln <= 0:
                player.hp -= ENEMY_DAMAGE
                invuln = HIT_COOLDOWN
                message = f"hit! hp={player.hp}"
                message_timer = 1.2

        if player.hp <= 0:
            end_state = "lose"
            running = False

        if message_timer > 0:
            message_timer -= dt
            msg = font.render(message, True, (235, 235, 235))
            screen.blit(msg, (8, maze.height * tile + 8 + 18))

        pygame.display.flip()

    if end_state in ("win", "lose"):
        action = run_end_menu(screen, clock, font, is_win=(end_state == "win"), player=player)
        if action == "menu":
            back_to_menu = True
        else:
            back_to_menu = False

    save_player_progress(player.name, player.coins)
    pygame.quit()
    return "menu" if back_to_menu else "quit"

def app():
    while True:
        res = main()
        if res != "menu":
            break


if __name__ == "__main__":
    app()
