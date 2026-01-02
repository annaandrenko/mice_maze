from __future__ import annotations
from pathlib import Path
from .player import Player

SAVE_FILE = Path("assets/player_save.txt")

def load_player() -> Player | None:
    if not SAVE_FILE.exists():
        return None
    try:
        data = SAVE_FILE.read_text(encoding="utf-8").splitlines()
        if len(data) >= 2:
            name = data[0].strip() or "Player"
            try:
                coins = int(data[1].strip())
            except ValueError:
                coins = 0
            return Player(x=3, y=1, name=name, coins=coins)
    except OSError:
        pass
    return None

def save_player(player: Player) -> None:
    SAVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SAVE_FILE.write_text(f"{player.name}\n{player.coins}\n", encoding="utf-8")
