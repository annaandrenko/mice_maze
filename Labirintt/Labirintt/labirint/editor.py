import pygame
from cells import Cell
from maze import Maze, generate_perfect_maze_cells
from main_pygame import load_sprites
from main_pygame import (
    DEFAULT_TILE, WALL_SYM, CHEESE_SYM, EXIT_SYM,
    HEAL_SYM, ENEMY_SYM, LEVELS, render_world
)

PLAYER_START_SYM = "S"
FLOOR_SYM = " "

class LevelEditor:
    def __init__(self, screen, clock, font):
        self.screen = screen
        self.clock = clock
        self.font = font
        self.hint_font = pygame.font.SysFont(None, 18)
        self.mode = "EDIT"
        self.test_x = 1
        self.test_y = 1
        self.start_pos = (1, 1)
        self.tile = DEFAULT_TILE
        self.sprites = load_sprites(self.tile)
        self.width = 31
        self.height = 15
        self.message = ""
        self.message_timer = 0

        self.maze = Maze([[Cell(WALL_SYM) for _ in range(self.width)]
                          for _ in range(self.height)])

        self.current_symbol = WALL_SYM

    def run(self):
        while True:
            self.clock.tick(60)
            result = self.handle_events()
            if result == "exit":
                return
            self.render()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "exit"

                elif event.key == pygame.K_c:
                    self.current_symbol = CHEESE_SYM
                elif event.key == pygame.K_x:
                    self.current_symbol = EXIT_SYM
                elif event.key == pygame.K_h:
                    self.current_symbol = HEAL_SYM
                elif event.key == pygame.K_e:
                    self.current_symbol = ENEMY_SYM
                elif event.key == pygame.K_w:
                    self.current_symbol = WALL_SYM
                elif event.key == pygame.K_SPACE:
                    self.current_symbol = " "
                elif event.key == pygame.K_l:
                    self.load_level("LVL_EDITOR.txt")
                elif event.key == pygame.K_g:
                    self.generate_maze(31, 15)
                elif event.key == pygame.K_p:
                    self.current_symbol = PLAYER_START_SYM
                elif event.key == pygame.K_t:
                    if self.mode == "EDIT":
                        self.mode = "TEST"
                        self.test_x, self.test_y = self.start_pos
                    else:
                        self.mode = "EDIT"
                elif event.key == pygame.K_F5:
                    self.save_level("LVL_EDITOR.txt")

                if self.mode == "TEST":
                    dx, dy = 0, 0
                    if event.key in (pygame.K_w, pygame.K_UP):
                        dy = -1
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        dy = 1
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        dx = -1
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        dx = 1

                    if dx or dy:
                        nx, ny = self.test_x + dx, self.test_y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            cell = self.maze.grid[ny][nx]

                            if cell.symbol != WALL_SYM:
                                if cell.symbol == CHEESE_SYM:
                                    cell.symbol = " "

                                self.test_x, self.test_y = nx, ny

                elif event.key == pygame.K_s:
                    self.save_level("LVL_EDITOR.txt")

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                gx, gy = mx // self.tile, my // self.tile

                if 0 <= gx < self.width and 0 <= gy < self.height:
                    if event.button == 1:
                        if self.current_symbol == PLAYER_START_SYM:
                            self.clear_symbol(PLAYER_START_SYM)
                            self.start_pos = (gx, gy)

                        if self.current_symbol == EXIT_SYM:
                            self.clear_symbol(EXIT_SYM)

                        self.maze.grid[gy][gx].symbol = self.current_symbol

                    elif event.button == 3:
                        self.maze.grid[gy][gx].symbol = " "

    def load_level(self, filename: str) -> None:
        path = LEVELS / filename
        if not path.exists():
            return

        lines = path.read_text(encoding="utf-8").splitlines()
        h = len(lines)
        w = max(len(line) for line in lines) if lines else 0
        norm = [line.ljust(w) for line in lines]

        self.width, self.height = w, h
        self.maze = Maze([[Cell(ch) for ch in row] for row in norm])

        pos = self.maze.find_symbol(PLAYER_START_SYM)
        if pos:
            self.start_pos = pos

    def render(self):
        from player import Player
        px, py = self.start_pos

        if self.mode == "TEST":
            px, py = self.test_x, self.test_y

        dummy_player = Player(px, py, "Editor", 0)

        render_world(
            self.screen,
            self.maze,
            dummy_player,
            enemies=[],
            sprites=self.sprites,
            tile=self.tile,
            font=self.font
        )

        hints = [
            "EDITOR MODE",
            "ESC- Back to menu  T- Toggle TEST mode",
            "LMB- place  RMB- erase",
            "W=wall  SPACE=floor  C=cheese  X=exit  P=start",
            "H=heal  E=enemy",
            "G-generate  L-load  S-save",
            "TEST: WASD/Arrows - move",
        ]

        y = 6
        for line in hints:
            surf = self.hint_font.render(line, True, (240, 240, 240))
            self.screen.blit(surf, (6, y))
            y += 18

        if self.message_timer > 0 and self.message:
            self.message_timer -= 1
            surf = self.font.render(self.message, True, (255, 120, 120))
            self.screen.blit(surf, (6, self.height * self.tile - 24))
        pygame.display.flip()

    def save_level(self, filename):
        start_count = self.count_symbol(PLAYER_START_SYM)
        exit_count = self.count_symbol(EXIT_SYM)

        if start_count != 1 or exit_count != 1:
            if start_count != 1 and exit_count != 1:
                self.show_message("Не можна зберегти: постав 1 старт (P) і 1 вихід (X).")
            elif start_count != 1:
                self.show_message("Не можна зберегти: постав 1 старт гравця (P).")
            else:
                self.show_message("Не можна зберегти: постав 1 вихід (X).")
            return

        LEVELS.mkdir(parents=True, exist_ok=True)
        path = LEVELS / filename
        with open(path, "w", encoding="utf-8") as f:
            for row in self.maze.grid:
                f.write("".join(cell.symbol for cell in row) + "\n")

        self.show_message("Рівень збережено", seconds=2)

    def generate_maze(self, w: int, h: int) -> None:
        grid, (sx, sy) = generate_perfect_maze_cells(w, h)
        self.maze = Maze(grid)
        self.width, self.height = self.maze.width, self.maze.height
        self.start_pos = (sx, sy)

    def clear_symbol(self, sym: str) -> None:
        for row in self.maze.grid:
            for cell in row:
                if cell.symbol == sym:
                    cell.symbol = FLOOR_SYM

    def count_symbol(self, sym: str) -> int:
        return sum(1 for row in self.maze.grid for cell in row if cell.symbol == sym)

    def show_message(self, text: str, seconds: float = 2.0) -> None:
        self.message = text
        self.message_timer = int(seconds * 60)  # якщо 60 FPS


def run_editor(screen, clock, font):
    editor = LevelEditor(screen, clock, font)
    editor.run()