# Labirint (Python port)

Console version of your C# Labirint game.

## Run

```bash
python -m labirint.main
```

## Checklist mapping ("Вимоги")

This port was adjusted to satisfy the typical Python lab checklist:

1. **Вивести ігрове поле на екран** → `Maze.render_gamepad()` / `Maze.render_plain()` (`labirint/maze.py`).
2. **Зчитати клавішу з клавіатури** → `get_key()` (`labirint/input_utils.py`), used in `game.run()`.
3. **Перемістити гравця на полі** → movement block in `game.run()` (`labirint/game.py`).
4. **Перевірити клітинку, на яку натрапив гравець** → checks for wall/door/key/exit in `game.run()`.
5. **Організувати ігровий цикл** → outer `while state != EXIT` and inner gameplay `while state == PLAYING` in `game.run()`.
6. **Створити та використати декілька власних функцій** → e.g. `make_countdown()`, `log()` (`labirint/utils.py`), `Maze.find_symbol()`.

### Python basics covered in code
- `str` → cell symbols, paths, user input.
- `int/float` → coordinates, coins, time counters.
- `bool` → flags like `SOUND_ENABLED` (`labirint/sound.py`).
- `NoneType` → countdown returns `None` when finished (`make_countdown()`), optional `current_level` (`labirint/game.py`).

### Conditionals
- `if/elif/else` → input handling and cell checks (`labirint/game.py`).
- `and/or/not` → bounds checks and sound enable checks.
- chained comparisons `a < b < c` → `0 <= nx < width` pattern (`labirint/game.py`).

### Loops
- `for` / `range` → rendering map and padding rows (`labirint/maze.py`).
- `while` → game + menu loops (`labirint/game.py`, `labirint/screens.py`).
- `continue` / `break` → movement + menu handling (`labirint/game.py`).
- `for ... else` → level validation (`show_level_selection`) and `Maze.find_symbol()`.

### Functions
- optional (keyword) parameters → `render_in_gamepad(..., *, prompt="")` and `make_countdown(start_minutes=..., start_seconds=...)`.
- `*` / `**` parameters → `log(*parts, sep=..., **kwargs)` (`labirint/utils.py`).
- `lambda` → numeric sorting of levels (`labirint/screens.py`).
- built-ins → `len`, `max`, `min`, `sum`, `sorted` used across modules.
- nested functions → `make_countdown()` returns inner `tick()`.

### Scope
- `global` → `set_option()` modifies global SETTINGS (`labirint/config.py`).
- `nonlocal` → countdown state inside `tick()` (`labirint/utils.py`).
## Controls
- Move: **WASD** or **Arrow keys**
- Pause: **P**
- Use bomb: **B**
- Back to menu: **ESC**

## Files
- Levels: `assets/Levels/LVL*.txt`
- Screens (ASCII UI): `assets/Screens/*.txt`
- Save: `assets/player_save.txt`
