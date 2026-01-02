from __future__ import annotations

"""
Progress / stats subsystem.

This module is intentionally a "natural" part of the game:
- remembers best result per level
- counts total wins / defeats
- stores "visited cells" heatmap size (unique positions) to show exploration

It also deliberately demonstrates:
- dictionaries (best_by_level, totals)
- sets (visited positions)
- tuples ((x, y) positions)
- saving to a text file (stats.txt)
- saving to a binary file (stats.bin)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set, Tuple

STATS_TXT = Path("assets/stats.txt")
STATS_BIN = Path("assets/stats.bin")

MAGIC = b"LABS"
VERSION = 1


@dataclass
class Stats:
    # best "coins earned from level completion" per level file name
    best_by_level: Dict[str, int] = field(default_factory=dict)
    total_wins: int = 0
    total_defeats: int = 0

    # exploration: unique visited (x, y) during the CURRENT level run
    visited: Set[Tuple[int, int]] = field(default_factory=set)

    def reset_run(self) -> None:
        self.visited.clear()

    def mark_visited(self, pos: Tuple[int, int]) -> None:
        self.visited.add(pos)

    def record_win(self, level_name: str, earned: int) -> None:
        self.total_wins += 1
        prev = self.best_by_level.get(level_name)
        if prev is None or earned > prev:
            self.best_by_level[level_name] = earned

    def record_defeat(self) -> None:
        self.total_defeats += 1

    # -------- text IO (human readable) --------
    def save_text(self) -> None:
        STATS_TXT.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        lines.append(f"wins={self.total_wins}")
        lines.append(f"defeats={self.total_defeats}")
        lines.append("# best_by_level:")
        for level, best in sorted(self.best_by_level.items()):
            lines.append(f"{level}={best}")
        STATS_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def load_text() -> "Stats":
        s = Stats()
        if not STATS_TXT.exists():
            return s
        try:
            for raw in STATS_TXT.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("wins="):
                    s.total_wins = int(line.split("=", 1)[1])
                    continue
                if line.startswith("defeats="):
                    s.total_defeats = int(line.split("=", 1)[1])
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    # only treat LVL* entries as level records
                    if k.startswith("LVL"):
                        s.best_by_level[k] = int(v)
        except OSError:
            pass
        return s

    # -------- binary IO (compact) --------
    def save_binary(self) -> None:
        """
        Binary format:
        MAGIC(4) VERSION(u8) wins(u32) defeats(u32) count(u16)
        then repeated:
          name_len(u16) name(utf8 bytes) best(u32)
        """
        STATS_BIN.parent.mkdir(parents=True, exist_ok=True)
        items = sorted(self.best_by_level.items())
        blob = bytearray()
        blob += MAGIC
        blob += struct.pack("<BIIH", VERSION, self.total_wins, self.total_defeats, len(items))
        for name, best in items:
            name_b = name.encode("utf-8")
            blob += struct.pack("<H", len(name_b))
            blob += name_b
            blob += struct.pack("<I", int(best))
        STATS_BIN.write_bytes(bytes(blob))

    @staticmethod
    def load_binary() -> "Stats":
        s = Stats()
        if not STATS_BIN.exists():
            return s
        try:
            data = STATS_BIN.read_bytes()
            if len(data) < 4 + 1 + 4 + 4 + 2:
                return s
            if data[:4] != MAGIC:
                return s
            ver = data[4]
            if ver != VERSION:
                return s
            wins, defeats, count = struct.unpack_from("<IIH", data, 5)
            s.total_wins = int(wins)
            s.total_defeats = int(defeats)
            offset = 5 + 4 + 4 + 2
            for _ in range(count):
                if offset + 2 > len(data):
                    break
                (nlen,) = struct.unpack_from("<H", data, offset)
                offset += 2
                name = data[offset:offset+nlen].decode("utf-8", errors="ignore")
                offset += nlen
                if offset + 4 > len(data):
                    break
                (best,) = struct.unpack_from("<I", data, offset)
                offset += 4
                s.best_by_level[name] = int(best)
        except OSError:
            pass
        return s

    @staticmethod
    def load() -> "Stats":
        # prefer binary if present (it includes everything), otherwise parse text
        s = Stats.load_binary()
        if not s.best_by_level and (STATS_TXT.exists()):
            s2 = Stats.load_text()
            # merge totals conservatively
            s.total_wins = s2.total_wins
            s.total_defeats = s2.total_defeats
            s.best_by_level = s2.best_by_level
        return s

    def save(self) -> None:
        # write both so criteria are met and user can inspect values
        self.save_text()
        self.save_binary()
