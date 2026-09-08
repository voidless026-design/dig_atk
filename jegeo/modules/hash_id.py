"""Hash generation, format identification, and a small demo dictionary check."""
from __future__ import annotations

import hashlib
import re

from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QLineEdit, QCheckBox, QVBoxLayout, QWidget,
)

from jegeo.modules.base import BaseModule
from jegeo.core.wordlist import COMMON_PASSWORDS

ALGOS = ["md5", "sha1", "sha256", "sha512", "blake2b", "sha3_256"]

_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")

_LENGTH_GUESSES = {
    32: ["MD5", "NTLM", "MD4"],
    40: ["SHA-1"],
    56: ["SHA-224", "SHA3-224"],
    64: ["SHA-256", "SHA3-256", "BLAKE2s"],
    96: ["SHA-384", "SHA3-384"],
    128: ["SHA-512", "SHA3-512", "BLAKE2b"],
}


def identify_hash(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("$2a$") or value.startswith("$2b$") or value.startswith("$2y$"):
        return ["bcrypt"]
    if value.startswith("$1$"):
        return ["MD5-crypt"]
    if value.startswith("$6$"):
        return ["SHA-512-crypt"]
    if value.startswith("$argon2"):
        return ["Argon2"]
    if not _HEX_RE.match(value):
        return ["unrecognized (not pure hex, not a known salted-hash prefix)"]
    return _LENGTH_GUESSES.get(len(value), [f"unrecognized ({len(value)} hex chars)"])


class HashIdModule(BaseModule):
    display_name = "Hash ID / Digest"
    glyph = "#"
    tagline = "Generate digests, fingerprint hash formats"
    notice = "Dictionary check uses a small built-in sample list — for testing your own hashes only."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        form = QFormLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Generate digest", "Identify hash format", "Check against sample dictionary"])
        self.mode_combo.currentTextChanged.connect(self._sync_visibility)
        form.addRow("MODE", self.mode_combo)

        self.algo_combo = QComboBox()
        self.algo_combo.addItems(ALGOS)
        form.addRow("ALGORITHM", self.algo_combo)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("text to hash, or a hash value to identify")
        form.addRow("INPUT", self.input_field)
        outer.addLayout(form)

        self.hint_lbl = QCheckBox("(dictionary check tries md5/sha1/sha256 of each sample word)")
        self.hint_lbl.setEnabled(False)
        outer.addWidget(self.hint_lbl)

        self._sync_visibility(self.mode_combo.currentText())
        return wrapper

    def _sync_visibility(self, mode: str):
        self.algo_combo.setEnabled(mode == "Generate digest")
        self.hint_lbl.setVisible(mode == "Check against sample dictionary")

    def make_task(self):
        mode = self.mode_combo.currentText()
        algo = self.algo_combo.currentText()
        value = self.input_field.text()

        def task(emit, is_cancelled):
            if not value:
                emit("input is empty", "error")
                return

            if mode == "Generate digest":
                h = hashlib.new(algo, value.encode("utf-8"))
                emit(f"{algo} digest:", "cyan")
                emit(f"  {h.hexdigest()}", "success")

            elif mode == "Identify hash format":
                guesses = identify_hash(value)
                emit(f"input length: {len(value.strip())} chars", "meta")
                emit("possible format(s):", "cyan")
                for g in guesses:
                    emit(f"  - {g}", "success")

            elif mode == "Check against sample dictionary":
                target = value.strip().lower()
                emit(f"checking {len(COMMON_PASSWORDS)} sample words against target hash...", "meta")
                found = None
                for i, word in enumerate(COMMON_PASSWORDS):
                    if is_cancelled():
                        emit("check aborted", "warn")
                        return
                    for algo_name in ("md5", "sha1", "sha256"):
                        digest = hashlib.new(algo_name, word.encode("utf-8")).hexdigest()
                        if digest == target:
                            found = (word, algo_name)
                            break
                    if found:
                        break
                if found:
                    word, algo_name = found
                    emit(f"MATCH: '{word}' ({algo_name})", "success")
                    emit("this hash corresponds to a trivially common password", "warn")
                else:
                    emit("no match in sample dictionary — not conclusive either way", "info")
            else:
                emit(f"unknown mode {mode!r}", "error")

        return task
