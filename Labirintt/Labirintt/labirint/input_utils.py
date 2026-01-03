from __future__ import annotations
import os, sys, time

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def get_key() -> str:
    if os.name == "nt":
        import msvcrt
        while True:
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                ch2 = msvcrt.getwch()
                mapping = {"H":"up","P":"down","K":"left","M":"right"}
                return mapping.get(ch2, "")
            if ch == "\x1b":
                return "esc"
            if ch in ("\r", "\n"):
                return "enter"
            return ch.lower()
    else:
        import termios, tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    mapping = {"A":"up","B":"down","C":"right","D":"left"}
                    return mapping.get(ch3, "esc")
                return "esc"
            if ch in ("\r", "\n"):
                return "enter"
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

def sleep(ms: int):
    time.sleep(ms/1000.0)
