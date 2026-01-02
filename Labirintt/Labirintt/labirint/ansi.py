from __future__ import annotations

RESET = "\x1b[0m"

FG = {
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    "bright_black": "\x1b[90m",
    "bright_white": "\x1b[97m",
}

def fg(name: str) -> str:
    return FG.get(name, "")

def color(text: str, name: str) -> str:
    c = fg(name)
    return f"{c}{text}{RESET}" if c else text


import re
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def strip_ansi(s: str) -> str:
    return _ANSI_RE.sub('', s)

def visible_len(s: str) -> int:
    return len(strip_ansi(s))
