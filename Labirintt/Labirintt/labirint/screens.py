from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Tuple

from .input_utils import clear, get_key
from .player import Player, Item
from .sound import beep
from .ansi import strip_ansi, visible_len

SCREENS_DIR = Path("assets/Screens")
LEVELS_DIR = Path("assets/Levels")
GAMEPAD_DIR = Path("assets/Gamepad")

_PAD_TOP_PATH = GAMEPAD_DIR / "padtop.txt"
_PAD_BOTTOM_PATH = GAMEPAD_DIR / "padbottom.txt"

INNER_W = 34
INNER_H = 10


def _read_screen(name: str) -> str:
    # Some files may start with UTF-8 BOM; strip it.
    txt = (SCREENS_DIR / name).read_text(encoding="utf-8")
    return txt.lstrip("\ufeff")


def _read_gamepad() -> Tuple[List[str], List[str]]:
    pad_top = _PAD_TOP_PATH.read_text(encoding="utf-8").splitlines()
    pad_bottom = _PAD_BOTTOM_PATH.read_text(encoding="utf-8").splitlines()
    return pad_top, pad_bottom


def _fit_line(s: str, width: int) -> str:
    # Keep ANSI codes intact for later; truncate based on visible length.
    if visible_len(s) <= width:
        return s + (" " * (width - visible_len(s)))
    plain = strip_ansi(s)
    # For screen ASCII we typically have no ANSI, so this is good enough.
    if len(plain) > width:
        plain = plain[:width]
    return plain + (" " * (width - len(plain)))


def render_in_gamepad(lines: List[str], *, prompt: str = "") -> str:
    """Render arbitrary text inside the MeowPad screen area (34x10)."""
    pad_top, pad_bottom = _read_gamepad()

    content: List[str] = []

    # Crop/pad to INNER_H. If prompt provided, reserve last line for it.
    lines = [ln.rstrip("\n") for ln in lines]
    if prompt:
        prompt_line = _fit_line(prompt, INNER_W)
        usable_h = INNER_H - 1
    else:
        prompt_line = ""
        usable_h = INNER_H

    # Prefer the top portion (menus are top-aligned); drop extra lines from bottom.
    body = lines[:usable_h]
    if len(body) < usable_h:
        body.extend([""] * (usable_h - len(body)))

    body = [_fit_line(ln, INNER_W) for ln in body]

    content.extend(body)
    if prompt:
        content.append(prompt_line)

    def wrap(line: str) -> str:
        # Exact wrapper matches maze.py
        return f"| |  {line} |  |"

    framed: List[str] = []
    framed.extend(pad_top)
    framed.extend(wrap(ln) for ln in content)
    framed.extend(pad_bottom)
    return "\n".join(framed)


def show_main_menu(player: Optional[Player] = None) -> str:
    clear()
    txt = _read_screen("MainMenu.txt")
    if player:
        txt = txt.replace("1. Iм’я:", f"1. Iм’я: {player.name}")
        txt = txt.replace("2. Обрати рiвень", "2. Обрати рiвень")  # keep as-is
    lines = txt.splitlines()
    frame = render_in_gamepad(lines, prompt="1-Start  2-Levels  3-Shop  4-Exit")
    print(frame)
    while True:
        k = get_key()
        if k in ("1", "2", "3", "4"):
            beep("click")
            return k


def show_level_selection(best_by_level: dict[str, int] | None = None) -> str:
    clear()
    txt = _read_screen("LevelSelection.txt")
    lines = txt.splitlines()
    # Use lambda to sort levels numerically by the trailing digits.
    lvls = sorted(
        (p.stem for p in LEVELS_DIR.glob("LVL*.txt")),
        key=lambda name: int("".join(ch for ch in name if ch.isdigit()) or 0),
    )
    best_by_level = best_by_level or {}
    # Natural extra info: show best result per level (dictionary lookup).
    info = [
        f"{i+1}) {lvl}  best: {best_by_level.get(lvl, '-')}"
        for i, lvl in enumerate(lvls[:6])
    ]
    insert_at = min(6, len(lines))
    # slicing demo: insert info lines into the screen template
    lines = lines[:insert_at] + [""] + info + lines[insert_at:]
    prompt = "1-6 choose level   ESC back"
    frame = render_in_gamepad(lines, prompt=prompt)
    print(frame)

    # Accept digits, but validate that the corresponding LVL exists.
    while True:
        k = get_key()
        if k == "esc":
            beep("click")
            return "esc"
        if k in ("1", "2", "3", "4", "5", "6"):
            # for/else demonstration: search in the available list
            wanted = f"LVL{k}"
            for lvl in lvls:
                if lvl == wanted:
                    beep("click")
                    return k
            else:
                # Not found: ignore input and keep listening
                beep("warn")
                continue


def show_shop_menu(player: Player) -> None:
    """Shop loop.

    Demonstrates:
    - while-loop game/menu cycles
    - None return (NoneType) through show_shop()
    """
    while True:
        item = show_shop(player)
        if item is None:
            return
        player.inventory.append(item)


def show_shop(player: Player) -> Optional[Item]:
    clear()
    txt = _read_screen("ShopMenu.txt")
    lines = txt.splitlines()

    prompt = "1-Bomb(15)  2-Magnet(20)  ESC back"
    frame = render_in_gamepad(lines, prompt=prompt)
    print(frame)
    while True:
        k = get_key()
        if k == "esc":
            beep("click")
            return None
        if k == "1":
            if player.coins >= 15:
                player.coins -= 15
                beep("success")
                return Item("Бомбочка", 15)
            beep("warn")
            return None
        if k == "2":
            if player.coins >= 20:
                player.coins -= 20
                beep("success")
                return Item("Магнiт", 20)
            beep("warn")
            return None


def show_pause_menu() -> str:
    clear()
    txt = _read_screen("PauseMenu.txt")
    lines = txt.splitlines()
    frame = render_in_gamepad(lines, prompt="1-Continue   2-To menu")
    print(frame)
    while True:
        k = get_key()
        if k in ("1", "2"):
            beep("click")
            return k


def show_victory(player: Player, coins_earned: int) -> str:
    clear()
    txt = _read_screen("VictoryScreen.txt")
    lines = txt.splitlines()

    # Insert coins line into a blank area if possible
    coins_line = f"+{coins_earned} coins"
    # Find a likely empty middle line to place it (line 4 is usually blank-ish).
    if len(lines) >= 6:
        lines[4] = lines[4][:2] + coins_line.center(max(0, len(lines[4]) - 4)) + lines[4][-2:]

    frame = render_in_gamepad(lines, prompt="1-Menu  2-Levels  3-Replay")
    print(frame)
    while True:
        k = get_key()
        if k in ("1", "2", "3"):
            beep("click")
            return k


def show_defeat(player: Player) -> str:
    clear()
    txt = _read_screen("DefeatScreen.txt")
    lines = txt.splitlines()
    frame = render_in_gamepad(lines, prompt="1-Retry  2-Menu  3-Levels")
    print(frame)
    while True:
        k = get_key()
        if k in ("1", "2", "3"):
            return k
