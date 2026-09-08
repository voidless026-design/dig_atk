"""Local storage for optional third-party API keys (currently: Shodan).

This panel never makes a network call itself — it only writes to
``~/.config/jegeo/settings.json`` on this machine. Keys entered here are
read by other modules (OSINT Intel's Shodan check) that explicitly say so.
"""
from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

from jegeo.core import settings
from jegeo.modules.base import BaseModule


class SettingsModule(BaseModule):
    display_name = "Settings"
    glyph = "⚙"
    tagline = "Local API key storage"
    notice = "Keys are written only to ~/.config/jegeo/settings.json on this machine and are never sent anywhere by this panel."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        form = QFormLayout(wrapper)

        self.shodan_input = QLineEdit()
        self.shodan_input.setEchoMode(QLineEdit.EchoMode.Password)
        if settings.get("shodan_api_key"):
            self.shodan_input.setPlaceholderText("(saved — leave blank to keep, or type a new key to replace)")
        else:
            self.shodan_input.setPlaceholderText("your Shodan API key (optional, enables OSINT Intel's Shodan check)")
        form.addRow("SHODAN KEY", self.shodan_input)

        return wrapper

    def make_task(self):
        new_key = self.shodan_input.text().strip()

        def task(emit, is_cancelled):
            if new_key:
                settings.set_key("shodan_api_key", new_key)
                emit("Shodan API key saved locally", "success")
            else:
                existing = settings.get("shodan_api_key", "")
                if existing:
                    emit("Shodan API key already configured (unchanged)", "info")
                else:
                    emit("no key entered — Shodan host lookup in OSINT Intel will stay disabled", "warn")
            emit(f"settings file: {settings.CONFIG_FILE}", "meta")

        return task
