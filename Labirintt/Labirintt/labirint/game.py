from __future__ import annotations

from enum import Enum, auto

from input_utils import clear, get_key
from maze import load_map, Maze
from player import Player
from save import load_player, save_player
from stats import Stats
from . import screens
from utils import make_countdown, log


class GameState(Enum):
    MAIN_MENU = auto()
    LEVEL_SELECTION = auto()
    SHOP_MENU = auto()
    PLAYING = auto()
    EXIT = auto()


def _reset_player_for_level(player: Player) -> None:
    player.x, player.y = 0, 0

LEVEL_TIME_MIN = 1
LEVEL_TIME_SEC = 30


def _level_path(level_filename: str) -> str:
    return f"assets/Levels/{level_filename}"


def run() -> None:
    player = load_player() or Player(x=3, y=1, name="Player", coins=0)
    stats = Stats.load()

    current_level: str | None = "LVL1.txt"
    state = GameState.MAIN_MENU

    while state != GameState.EXIT:
        if state == GameState.MAIN_MENU:
            choice = screens.show_main_menu(player)
            if choice == "1":
                state = GameState.PLAYING
            elif choice == "2":
                state = GameState.LEVEL_SELECTION
            elif choice == "3":
                state = GameState.SHOP_MENU
            elif choice == "4":
                state = GameState.EXIT

        elif state == GameState.LEVEL_SELECTION:
            choice = screens.show_level_selection(stats.best_by_level)
            if choice == "esc":
                state = GameState.MAIN_MENU
            else:
                current_level = f"LVL{choice}.txt"
                state = GameState.PLAYING

        elif state == GameState.SHOP_MENU:
            screens.show_shop_menu(player)
            save_player(player)
            state = GameState.MAIN_MENU

        elif state == GameState.PLAYING:
            assert current_level is not None
            grid = load_map(_level_path(current_level))
            maze = Maze(grid)
            stats.reset_run()
            spawn = maze.random_empty_cell() or (0, 0)
            player.x, player.y = spawn
            stats.mark_visited((player.x, player.y))

            tick = make_countdown(LEVEL_TIME_MIN, LEVEL_TIME_SEC)

            while state == GameState.PLAYING:
                remaining = tick()
                if remaining is None:
                    # defeat
                    stats.record_defeat()
                    stats.save()
                    choice = screens.show_defeat(player)
                    if choice == "1":
                        _reset_player_for_level(player)
                        state = GameState.PLAYING
                    elif choice == "3":
                        state = GameState.LEVEL_SELECTION
                    else:
                        state = GameState.MAIN_MENU
                    break

                minutes, seconds = remaining

                urgent = (minutes == 0 and seconds <= 15)

                clear()
                print(maze.render_gamepad(player, minutes, seconds, urgent=urgent))

                k = get_key()

                if k == "esc":
                    state = GameState.MAIN_MENU
                    break

                if k == "p":
                    pm = screens.show_pause_menu()
                    if pm == "2":
                        state = GameState.MAIN_MENU
                        break
                    continue

                if k == "b":
                    player.use_bomb(maze.grid)
                    continue

                dx, dy = 0, 0
                if k in ("w", "up"):
                    dy = -1
                elif k in ("s", "down"):
                    dy = 1
                elif k in ("a", "left"):
                    dx = -1
                elif k in ("d", "right"):
                    dx = 1
                else:
                    continue

                nx, ny = player.x + dx, player.y + dy
                if not (0 <= nx < maze.width and 0 <= ny < maze.height):
                    continue

                next_cell = maze.cell_at(nx, ny)
                if not next_cell.walkable:
                    continue

                sym = next_cell.symbol

                # exit
                if sym == "X":
                    player.x, player.y = nx, ny


                    stats.mark_visited((player.x, player.y))
                    coins_earned = minutes * 10 + (seconds // 5)
                    player.coins += coins_earned
                    save_player(player)

                    stats.record_win(current_level.replace('.txt',''), coins_earned)
                    stats.save()

                    log("Level complete:", current_level, "earned", coins_earned, "coins")

                    choice = screens.show_victory(player, coins_earned)
                    if choice == "3":
                        _reset_player_for_level(player)
                        state = GameState.PLAYING
                    elif choice == "2":
                        state = GameState.LEVEL_SELECTION
                    else:
                        state = GameState.MAIN_MENU
                    break

                player.x, player.y = nx, ny
                stats.mark_visited((player.x, player.y))
                save_player(player)

    save_player(player)
    clear()
    print("Bye!")
