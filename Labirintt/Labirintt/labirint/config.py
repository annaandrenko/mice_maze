"""Project-wide configuration.

This module intentionally demonstrates:
- global scope (`global` keyword)
- NoneType usage (optional config values)
"""

from __future__ import annotations

from typing import Any, Optional


# Global settings dictionary (demonstrates `global` usage in setters)
SETTINGS: dict[str, Any] = {
    "sound": True,
    "debug": False,
    # Optional value; None means "no enforced fps cap".
    "fps_cap": None,  # type: Optional[int]
}


def set_option(name: str, value: Any) -> None:
    """Set a global option.

    Uses `global` to make the educational point explicit.
    """
    global SETTINGS
    SETTINGS[name] = value


def get_option(name: str, default: Any = None) -> Any:
    return SETTINGS.get(name, default)
