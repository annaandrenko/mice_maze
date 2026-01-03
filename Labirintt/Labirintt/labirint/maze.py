from __future__ import annotations

from typing import List, Tuple
import random

from cells import Cell
from player import Player
from ansi import color, strip_ansi, visible_len


INNER_W = 34
INNER_H = 10


def load_map(path: str) -> List[List[Cell]]:
    from cell_definer import cell_from_char

    grid: List[List[Cell]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f.read().splitlines():
            grid.append([cell_from_char(ch) for ch in line])

    w = max((len(r) for r in grid), default=0)
    for r in grid:
        if len(r) < w:
            r.extend([Cell() for _ in range(w - len(r))])
    return grid

from collections import deque


def generate_perfect_maze_cells(width: int, height: int) -> tuple[list[list[Cell]], tuple[int, int]]:
    from cell_definer import cell_from_char

    if width % 2 == 0:
        width += 1
    if height % 2 == 0:
        height += 1

    WALL = "#"
    FLOOR = " "
    EXIT = "X"

    raw = [[WALL for _ in range(width)] for _ in range(height)]

    sx = random.randrange(1, width, 2)
    sy = random.randrange(1, height, 2)
    raw[sy][sx] = FLOOR

    stack = [(sx, sy)]
    dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]

    while stack:
        x, y = stack[-1]
        random.shuffle(dirs)
        carved = False

        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 1 <= nx < width - 1 and 1 <= ny < height - 1 and raw[ny][nx] == WALL:
                raw[y + dy // 2][x + dx // 2] = FLOOR
                raw[ny][nx] = FLOOR
                stack.append((nx, ny))
                carved = True
                break

        if not carved:
            stack.pop()

    q = deque([(sx, sy)])
    dist = [[-1] * width for _ in range(height)]
    dist[sy][sx] = 0
    farthest = (sx, sy)

    while q:
        x, y = q.popleft()

        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if raw[ny][nx] == FLOOR and dist[ny][nx] == -1:
                    dist[ny][nx] = dist[y][x] + 1
                    q.append((nx, ny))

                    fx, fy = farthest
                    if dist[ny][nx] > dist[fy][fx]:
                        farthest = (nx, ny)

    ex, ey = farthest
    raw[ey][ex] = EXIT
    grid: list[list[Cell]] = []
    for row in raw:
        grid.append([cell_from_char(ch) for ch in row])

    return grid, (sx, sy)


class Maze:
    def __init__(self, grid: List[List[Cell]]) -> None:
        self.grid = grid

    @property
    def height(self) -> int:
        return len(self.grid)

    @property
    def width(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    def cell_at(self, x: int, y: int) -> Cell:
        return self.grid[y][x]

    def set_cell(self, x: int, y: int, cell: Cell) -> None:
        self.grid[y][x] = cell

    def find_symbol(self, symbol: str):
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell.symbol == symbol:
                    return x, y
            else:
                continue
        else:
            return None

    def random_empty_cell(self) -> tuple[int, int] | None:
        empties: list[tuple[int, int]] = []
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell.walkable and cell.symbol == " ":
                    empties.append((x, y))
        if not empties:
            return None
        return random.choice(empties)

    def _render_cell(self, x: int, y: int, player: Player) -> str:
        if x == player.x and y == player.y:
            return color("●", "yellow")
        return self.grid[y][x].render()

    def render_plain(self, player: Player, minutes: int, seconds: int, urgent: bool = False) -> str:
        time_txt = f"{minutes:02d}:{seconds:02d}"
        if urgent:
            time_txt = color(time_txt, "red")

        bombs = sum(1 for it in player.inventory if it.name.lower().startswith("бом"))
        hud = f"Time: {time_txt} | Player: {player.name} | Coins: {player.coins} | Bombs: {bombs}"
        out = [hud, ""]
        for y in range(self.height):
            out.append("".join(self._render_cell(x, y, player) for x in range(self.width)))
        out.append("")
        out.append("Controls: WASD/Arrows move | P pause | B bomb | ESC menu")
        return "\n".join(out)


    def _fit_text(self, s: str, width: int) -> str:
        if visible_len(s) <= width:
            return s + (" " * (width - visible_len(s)))
        plain = strip_ansi(s)
        if len(plain) > width:
            plain = plain[:width]
        return plain + (" " * (width - len(plain)))

    def _view_bounds(self, player: Player, vw: int, vh: int) -> Tuple[int, int]:
        x0 = player.x - vw // 2
        y0 = player.y - vh // 2
        if self.width > vw:
            x0 = max(0, min(x0, self.width - vw))
        else:
            x0 = 0
        if self.height > vh:
            y0 = max(0, min(y0, self.height - vh))
        else:
            y0 = 0
        return x0, y0

    def render_gamepad(self, player: Player, minutes: int, seconds: int, urgent: bool = False) -> str:
        pad_top, pad_bottom = self._read_gamepad()

        time_txt = f"{minutes:02d}:{seconds:02d}"
        if urgent:
            time_txt = color(time_txt, "red")

        bombs = sum(1 for it in player.inventory if it.name.lower().startswith("бом"))

        # Inner screen lines
        x0, y0 = self._view_bounds(player, INNER_W, INNER_H)

        header = f"{player.name}  ⏱ {time_txt}  💰 {player.coins}  💣 {bombs}"
        header = self._fit_text(header, INNER_W)

        view_lines: List[str] = [header]
        x1 = x0 + INNER_W  # slice end
        for row_i in range(INNER_H - 1):
            y = y0 + row_i
            if not (0 <= y < self.height):
                view_lines.append(" " * INNER_W)
                continue

            xL = max(0, x0)
            xR = min(self.width, x1)
            row_slice = self.grid[y][xL:xR]

            rendered_mid = [
                self._render_cell(xL + i, y, player)
                for i, _cell in enumerate(row_slice)
            ]

            left_pad = [" "] * max(0, 0 - x0)
            right_pad = [" "] * max(0, x1 - self.width)

            view_lines.append("".join(left_pad + rendered_mid + right_pad)[:INNER_W])

