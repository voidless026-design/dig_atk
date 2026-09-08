"""Local storage for optional third-party API keys (Shodan, AbuseIPDB).

This panel never makes a network call itself — it only writes to
``~/.config/jegeo/settings.json`` on this machine. Keys entered here are
read by other modules (OSINT Intel's Shodan and AbuseIPDB checks) that
explicitly say so.
"""
from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

from jegeo.core import settings
from jegeo.modules.base import BaseModule

# (settings key, field label, description used in the placeholder/blank-key message)
API_KEYS = [
    ("shodan_api_key", "SHODAN KEY", "Shodan", "enables OSINT Intel's Shodan host lookup"),
    ("abuseipdb_api_key", "ABUSEIPDB KEY", "AbuseIPDB", "enables OSINT Intel's AbuseIPDB reputation check"),
]


class SettingsModule(BaseModule):
    display_name = "Settings"
    glyph = "⚙"
    tagline = "Local API key storage"
    notice = "Keys are written only to ~/.config/jegeo/settings.json on this machine and are never sent anywhere by this panel."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        form = QFormLayout(wrapper)

        self._inputs = {}
        for key, label, name, purpose in API_KEYS:
            field = QLineEdit()
            field.setEchoMode(QLineEdit.EchoMode.Password)
            if settings.get(key):
                field.setPlaceholderText("(saved — leave blank to keep, or type a new key to replace)")
            else:
                field.setPlaceholderText(f"your {name} API key (optional, {purpose})")
            form.addRow(label, field)
            self._inputs[key] = field

        return wrapper

    def make_task(self):
        new_values = {key: field.text().strip() for key, field in self._inputs.items()}

        def task(emit, is_cancelled):
            for key, label, name, purpose in API_KEYS:
                new_key = new_values[key]
                if new_key:
                    settings.set_key(key, new_key)
                    emit(f"{name} API key saved locally", "success")
                else:
                    existing = settings.get(key, "")
                    if existing:
                        emit(f"{name} API key already configured (unchanged)", "info")
                    else:
                        emit(f"no {name} key entered — {purpose.split(' ', 1)[1]} will stay disabled", "warn")
            emit(f"settings file: {settings.CONFIG_FILE}", "meta")

        return task
