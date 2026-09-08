"""Encode/decode & encrypt/decrypt toolkit: base64, hex, ROT13, XOR, AES-256-GCM."""
from __future__ import annotations

import base64
import codecs
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QLineEdit, QPlainTextEdit, QRadioButton,
    QHBoxLayout, QVBoxLayout, QWidget,
)

from jegeo.modules.base import BaseModule

PBKDF2_ITERATIONS = 200_000
SALT_LEN = 16
NONCE_LEN = 12


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def aes_encrypt(plaintext: str, password: str) -> str:
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = _derive_key(password, salt)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(salt + nonce + ct).decode("ascii")


def aes_decrypt(blob_b64: str, password: str) -> str:
    raw = base64.b64decode(blob_b64.strip())
    salt, nonce, ct = raw[:SALT_LEN], raw[SALT_LEN:SALT_LEN + NONCE_LEN], raw[SALT_LEN + NONCE_LEN:]
    key = _derive_key(password, salt)
    pt = AESGCM(key).decrypt(nonce, ct, None)
    return pt.decode("utf-8")


def xor_bytes(data: bytes, key: str) -> bytes:
    kb = key.encode("utf-8")
    if not kb:
        raise ValueError("XOR key must not be empty")
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data))


class CryptoToolkitModule(BaseModule):
    display_name = "Crypto Toolkit"
    glyph = "⚿"
    tagline = "Encode / decode / encrypt / decrypt"

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        form = QFormLayout()
        self.cipher_combo = QComboBox()
        self.cipher_combo.addItems([
            "Base64", "Hex", "ROT13", "XOR (key)", "AES-256-GCM (password)",
        ])
        self.cipher_combo.currentTextChanged.connect(self._sync_key_visibility)
        form.addRow("CIPHER", self.cipher_combo)

        mode_row = QHBoxLayout()
        self.radio_encode = QRadioButton("Encode / Encrypt")
        self.radio_decode = QRadioButton("Decode / Decrypt")
        self.radio_encode.setChecked(True)
        mode_row.addWidget(self.radio_encode)
        mode_row.addWidget(self.radio_decode)
        mode_row.addStretch(1)
        form.addRow("MODE", self._wrap(mode_row))

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("key / password (XOR & AES only)")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("KEY", self.key_input)
        outer.addLayout(form)

        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText("input text...")
        self.input_text.setFixedHeight(90)
        outer.addWidget(self.input_text)

        self._sync_key_visibility(self.cipher_combo.currentText())
        return wrapper

    @staticmethod
    def _wrap(layout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def _sync_key_visibility(self, cipher_name: str):
        needs_key = cipher_name.startswith("XOR") or cipher_name.startswith("AES")
        self.key_input.setEnabled(needs_key)

    def make_task(self):
        cipher = self.cipher_combo.currentText()
        encode_mode = self.radio_encode.isChecked()
        key = self.key_input.text()
        data = self.input_text.toPlainText()

        def task(emit, is_cancelled):
            emit(f"cipher: {cipher}  |  mode: {'ENCODE/ENCRYPT' if encode_mode else 'DECODE/DECRYPT'}", "meta")
            try:
                if cipher == "Base64":
                    out = (
                        base64.b64encode(data.encode("utf-8")).decode("ascii")
                        if encode_mode else
                        base64.b64decode(data.strip()).decode("utf-8", errors="replace")
                    )
                elif cipher == "Hex":
                    out = (
                        data.encode("utf-8").hex()
                        if encode_mode else
                        bytes.fromhex(data.strip()).decode("utf-8", errors="replace")
                    )
                elif cipher == "ROT13":
                    out = codecs.encode(data, "rot_13")
                elif cipher == "XOR (key)":
                    if not key:
                        raise ValueError("XOR requires a key")
                    if encode_mode:
                        out = base64.b64encode(xor_bytes(data.encode("utf-8"), key)).decode("ascii")
                    else:
                        out = xor_bytes(base64.b64decode(data.strip()), key).decode("utf-8", errors="replace")
                elif cipher == "AES-256-GCM (password)":
                    if not key:
                        raise ValueError("AES requires a password")
                    out = aes_encrypt(data, key) if encode_mode else aes_decrypt(data, key)
                else:
                    raise ValueError(f"unknown cipher {cipher!r}")
            except InvalidTag:
                emit("decryption failed: wrong password or corrupted/tampered data", "error")
                return
            except Exception as exc:
                emit(f"operation failed: {exc}", "error")
                return

            emit("result:", "cyan")
            for line in out.splitlines() or [""]:
                emit(f"  {line}", "success")

        return task
