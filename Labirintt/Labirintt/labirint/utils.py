"""Small helpers used across the project.

This file is intentionally written to satisfy educational checklist items:
- custom functions
- optional keyword parameters
- *args / **kwargs
- lambda usage (in callers)
- nested functions and `nonlocal`
"""

from __future__ import annotations

import time
from typing import Callable, Optional


def log(*parts: object, sep: str = " ", end: str = "\n", **kwargs: object) -> None:
    """A tiny logger.

    Demonstrates:
    - `*parts` (variadic positional parameters)
    - optional keyword parameters (sep/end)
    - `**kwargs` forwarded to print
    """
    print(*parts, sep=sep, end=end, **kwargs)


def make_countdown(start_minutes: int = 1, start_seconds: int = 30) -> Callable[[], Optional[tuple[int, int]]]:
    """Return a `tick()` function that decreases time each second.

    - Demonstrates nested function + `nonlocal`.
    - Returns None when the timer is finished (NoneType requirement).
    """

    minutes = int(start_minutes)
    seconds = int(start_seconds)
    last_tick = time.time()

    def tick() -> Optional[tuple[int, int]]:
        nonlocal minutes, seconds, last_tick

        now = time.time()
        if now - last_tick < 1:
            return minutes, seconds

        last_tick = now
        seconds -= 1
        if seconds < 0:
            seconds = 59
            minutes -= 1

        # Finished
        if minutes < 0:
            return None

        return minutes, seconds

    return tick
