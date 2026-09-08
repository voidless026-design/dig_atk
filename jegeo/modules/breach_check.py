"""Password breach exposure check via the HaveIBeenPwned Pwned Passwords API.

Uses k-anonymity: only the first 5 hex characters of the password's SHA-1
hash are sent. The API returns every suffix that shares that prefix, and
the match is found locally — the full password, and even the full hash,
never leave this machine.
"""
from __future__ import annotations

import hashlib

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

from jegeo.core import http
from jegeo.modules.base import BaseModule

PWNED_RANGE_URL = "https://api.pwnedpasswords.com/range/{}"


class BreachCheckModule(BaseModule):
    display_name = "Breach Check"
    glyph = "⊘"
    tagline = "k-anonymity password exposure lookup"
    notice = "Only a 5-character SHA-1 prefix is sent to haveibeenpwned.com — your password never leaves this machine."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        form = QFormLayout(wrapper)
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setPlaceholderText("password to check")
        form.addRow("PASSWORD", self.pw_input)
        return wrapper

    def make_task(self):
        password = self.pw_input.text()
        if not password:
            raise ValueError("enter a password to check")

        sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]

        def task(emit, is_cancelled):
            emit(f"SHA-1 prefix: {prefix}... (only this is sent)", "meta")
            emit("querying haveibeenpwned.com Pwned Passwords range API...", "meta")
            try:
                text = http.get_text(PWNED_RANGE_URL.format(prefix))
            except Exception as exc:
                emit(f"lookup failed: {exc}", "error")
                return

            count = 0
            for line in text.splitlines():
                parts = line.strip().split(":")
                if len(parts) == 2 and parts[0] == suffix:
                    count = int(parts[1])
                    break

            if count > 0:
                emit(f"FOUND in known breaches: seen {count:,} time(s)", "error")
                emit("this password should not be used anywhere", "warn")
            else:
                emit("not found in the Pwned Passwords dataset", "success")
                emit("(a clean result isn't a strength guarantee — pair with Password Audit)", "meta")

        return task
