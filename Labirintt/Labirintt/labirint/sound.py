from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Lightweight, dependency-free sound layer.
# - On Windows: uses winsound (built-in) for beeps and wav.
# - Elsewhere: falls back to terminal bell (\a) where supported.
#
# You can disable all sounds by setting:
#   LABIRINT_SOUND=0

from .config import get_option


SOUND_ENABLED = os.environ.get("LABIRINT_SOUND", "1") not in ("0", "false", "False")


def _terminal_bell() -> None:
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        pass


def beep(kind: str = "click") -> None:
    if not SOUND_ENABLED or not bool(get_option("sound", True)):
        return
    try:
        import winsound  # type: ignore
        if kind == "warn":
            winsound.Beep(880, 120)
        elif kind == "success":
            winsound.Beep(660, 120)
            winsound.Beep(880, 120)
        else:
            winsound.Beep(600, 80)
        return
    except Exception:
        _terminal_bell()


def play_wav(path: str) -> None:
    if not SOUND_ENABLED:
        return
    try:
        import winsound
        p = Path(path)
        if p.exists():
            winsound.PlaySound(str(p), winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            beep()
    except Exception:
        _terminal_bell()


def play_background_music(path: str) -> None:
    return


def play_sfx(_path: str) -> None:
    beep()
