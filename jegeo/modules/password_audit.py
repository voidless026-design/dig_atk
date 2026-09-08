"""Local, offline password strength estimation — nothing leaves the machine."""
from __future__ import annotations

import math
import re

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

from jegeo.modules.base import BaseModule
from jegeo.core.wordlist import COMMON_PASSWORDS

_COMMON_SET = set(COMMON_PASSWORDS)

_KEYBOARD_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890"]


def _has_keyboard_walk(pw: str, min_run: int = 4) -> bool:
    lower = pw.lower()
    for row in _KEYBOARD_ROWS:
        for i in range(len(row) - min_run + 1):
            if row[i:i + min_run] in lower:
                return True
    return False


def _has_repeated_run(pw: str, min_run: int = 4) -> bool:
    run = 1
    for i in range(1, len(pw)):
        run = run + 1 if pw[i] == pw[i - 1] else 1
        if run >= min_run:
            return True
    return False


def _has_sequential_digits(pw: str, min_run: int = 4) -> bool:
    digits = "0123456789"
    return _has_keyboard_walk(pw, min_run) or any(
        digits[i:i + min_run] in pw or digits[i:i + min_run][::-1] in pw
        for i in range(len(digits) - min_run + 1)
    )


def analyze(password: str) -> dict:
    length = len(password)
    classes = {
        "lower": bool(re.search(r"[a-z]", password)),
        "upper": bool(re.search(r"[A-Z]", password)),
        "digit": bool(re.search(r"\d", password)),
        "symbol": bool(re.search(r"[^a-zA-Z0-9]", password)),
    }
    charset_size = (
        26 * classes["lower"] + 26 * classes["upper"]
        + 10 * classes["digit"] + 33 * classes["symbol"]
    )
    entropy = length * math.log2(charset_size) if charset_size and length else 0.0

    flags = []
    if password.lower() in _COMMON_SET:
        flags.append("exact match in common-password sample list")
        entropy = min(entropy, 10.0)
    if _has_keyboard_walk(password):
        flags.append("contains a keyboard-walk pattern (e.g. qwerty, asdf)")
    if _has_repeated_run(password):
        flags.append("contains 4+ repeated characters in a row")
    if _has_sequential_digits(password):
        flags.append("contains a sequential run (e.g. 1234, 4321)")
    if length < 8:
        flags.append("shorter than 8 characters")

    if entropy < 28 or length < 6:
        rating = "VERY WEAK"
    elif entropy < 36:
        rating = "WEAK"
    elif entropy < 60:
        rating = "MODERATE"
    elif entropy < 80:
        rating = "STRONG"
    else:
        rating = "VERY STRONG"

    # Ballpark offline crack-time estimates at two illustrative guess rates.
    def crack_time(guesses_per_sec: float) -> str:
        if entropy <= 0:
            return "instant"
        seconds = (2 ** entropy) / 2 / guesses_per_sec
        return _format_duration(seconds)

    return {
        "length": length,
        "classes": classes,
        "entropy": entropy,
        "rating": rating,
        "flags": flags,
        "crack_fast": crack_time(1e10),   # e.g. GPU cracking a fast unsalted hash
        "crack_slow": crack_time(1e4),    # e.g. a well-salted, stretched hash (bcrypt-ish)
    }


def _format_duration(seconds: float) -> str:
    units = [
        ("centuries", 60 * 60 * 24 * 365 * 100),
        ("years", 60 * 60 * 24 * 365),
        ("days", 60 * 60 * 24),
        ("hours", 60 * 60),
        ("minutes", 60),
        ("seconds", 1),
    ]
    if seconds < 1:
        return "under a second"
    for name, size in units:
        if seconds >= size:
            return f"~{seconds / size:,.1f} {name}"
    return "under a second"


class PasswordAuditModule(BaseModule):
    display_name = "Password Audit"
    glyph = "⛨"
    tagline = "Offline entropy & weakness analysis"
    notice = "Fully local — the password you enter is never written to disk or sent anywhere."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        form = QFormLayout(wrapper)
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setPlaceholderText("password to analyze")
        form.addRow("PASSWORD", self.pw_input)
        return wrapper

    def make_task(self):
        password = self.pw_input.text()

        def task(emit, is_cancelled):
            if not password:
                emit("no password entered", "error")
                return
            result = analyze(password)

            emit(f"length: {result['length']} characters", "info")
            classes = result["classes"]
            used = ", ".join(k for k, v in classes.items() if v) or "none"
            emit(f"character classes used: {used}", "info")
            emit(f"estimated entropy: {result['entropy']:.1f} bits", "info")

            level = result["rating"]
            level_style = {
                "VERY WEAK": "error", "WEAK": "error", "MODERATE": "warn",
                "STRONG": "success", "VERY STRONG": "success",
            }[level]
            emit(f"RATING: {level}", level_style)

            if result["flags"]:
                emit("issues found:", "warn")
                for f in result["flags"]:
                    emit(f"  - {f}", "warn")
            else:
                emit("no obvious weaknesses detected by these heuristics", "success")

            emit("illustrative offline crack-time estimates:", "cyan")
            emit(f"  fast hash / GPU cluster (~1e10 guesses/s): {result['crack_fast']}", "info")
            emit(f"  slow/stretched hash (~1e4 guesses/s):      {result['crack_slow']}", "info")
            emit("(estimates assume worst-case brute force at the analyzed entropy)", "meta")

        return task
