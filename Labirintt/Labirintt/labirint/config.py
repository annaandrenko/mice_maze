from __future__ import annotations

from typing import Any

SETTINGS: dict[str, Any] = {
    "sound": True,
    "debug": False,
    "fps_cap": None,  # type: Optional[int]
}


def set_option(name: str, value: Any) -> None:
    global SETTINGS
    SETTINGS[name] = value


def get_option(name: str, default: Any = None) -> Any:
    return SETTINGS.get(name, default)
