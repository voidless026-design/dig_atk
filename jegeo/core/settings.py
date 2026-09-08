"""Local, file-backed storage for optional third-party API keys.

Nothing here ever makes a network call — it only reads/writes
``~/.config/jegeo/settings.json`` on this machine, with permissions
restricted to the owner. Modules that use an online service with an
optional API key (currently: Shodan) read their key through ``get()``.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "jegeo"
CONFIG_FILE = CONFIG_DIR / "settings.json"


def load() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    try:
        os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def get(key: str, default=None):
    return load().get(key, default)


def set_key(key: str, value: str) -> None:
    data = load()
    data[key] = value
    save(data)
