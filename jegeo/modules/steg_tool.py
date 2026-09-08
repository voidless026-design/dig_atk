"""LSB steganography: hide/reveal a text message inside a PNG image."""
from __future__ import annotations

import os

from PIL import Image

from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from jegeo.modules.base import BaseModule

_HEADER_BITS = 32  # message length, big-endian, stored in the first 32 bits


def _to_bits(data: bytes) -> list[int]:
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _from_bits(bits: list[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | b
        out.append(byte)
    return bytes(out)


def embed_message(in_path: str, message: str, out_path: str) -> int:
    img = Image.open(in_path).convert("RGB")
    payload = message.encode("utf-8")
    header = len(payload).to_bytes(4, "big")
    bits = _to_bits(header) + _to_bits(payload)

    capacity = img.width * img.height * 3
    if len(bits) > capacity:
        raise ValueError(
            f"message too large: needs {len(bits)} bits, image only holds {capacity}"
        )

    pixels = img.load()
    idx = 0
    for y in range(img.height):
        for x in range(img.width):
            if idx >= len(bits):
                break
            r, g, b = pixels[x, y]
            channels = [r, g, b]
            for c in range(3):
                if idx < len(bits):
                    channels[c] = (channels[c] & ~1) | bits[idx]
                    idx += 1
            pixels[x, y] = tuple(channels)
        if idx >= len(bits):
            break

    img.save(out_path, "PNG")
    return len(payload)


def extract_message(in_path: str) -> str:
    img = Image.open(in_path).convert("RGB")
    pixels = img.load()

    header_bits: list[int] = []
    idx = 0
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels[x, y]
            for c in (r, g, b):
                if idx < _HEADER_BITS:
                    header_bits.append(c & 1)
                    idx += 1
            if idx >= _HEADER_BITS:
                break
        if idx >= _HEADER_BITS:
            break

    msg_len = int.from_bytes(_from_bits(header_bits), "big")
    total_bits_needed = _HEADER_BITS + msg_len * 8
    capacity = img.width * img.height * 3
    if msg_len <= 0 or total_bits_needed > capacity:
        raise ValueError("no hidden message found (or file is not a JEGEO-embedded PNG)")

    all_bits: list[int] = []
    idx = 0
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = pixels[x, y]
            for c in (r, g, b):
                if idx < total_bits_needed:
                    all_bits.append(c & 1)
                    idx += 1
            if idx >= total_bits_needed:
                break
        if idx >= total_bits_needed:
            break

    payload_bits = all_bits[_HEADER_BITS:total_bits_needed]
    return _from_bits(payload_bits).decode("utf-8", errors="replace")


class StegToolModule(BaseModule):
    display_name = "Steganography"
    glyph = "◐"
    tagline = "Hide / reveal text inside PNG images"
    notice = "LSB steganography is easily detected by dedicated analysis — for learning & CTFs, not real secrecy."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        form = QFormLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Embed message", "Extract message"])
        self.mode_combo.currentTextChanged.connect(self._sync_visibility)
        form.addRow("MODE", self.mode_combo)

        in_row = QHBoxLayout()
        self.in_path_edit = QLineEdit()
        self.in_path_edit.setPlaceholderText("source .png")
        browse_in = QPushButton("BROWSE")
        browse_in.clicked.connect(self._browse_in)
        in_row.addWidget(self.in_path_edit)
        in_row.addWidget(browse_in)
        form.addRow("IMAGE", self._wrap(in_row))

        out_row = QHBoxLayout()
        self.out_path_edit = QLineEdit()
        self.out_path_edit.setPlaceholderText("output .png (embed mode only)")
        browse_out = QPushButton("BROWSE")
        browse_out.clicked.connect(self._browse_out)
        out_row.addWidget(self.out_path_edit)
        out_row.addWidget(browse_out)
        self.out_row_widget = self._wrap(out_row)
        form.addRow("SAVE AS", self.out_row_widget)
        outer.addLayout(form)

        self.message_edit = QPlainTextEdit()
        self.message_edit.setPlaceholderText("secret message to embed...")
        self.message_edit.setFixedHeight(70)
        outer.addWidget(self.message_edit)

        self._sync_visibility(self.mode_combo.currentText())
        return wrapper

    @staticmethod
    def _wrap(layout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def _sync_visibility(self, mode: str):
        embed = mode == "Embed message"
        self.out_row_widget.setEnabled(embed)
        self.message_edit.setEnabled(embed)

    def _browse_in(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PNG image", "", "PNG Images (*.png)")
        if path:
            self.in_path_edit.setText(path)

    def _browse_out(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PNG as", "", "PNG Images (*.png)")
        if path:
            self.out_path_edit.setText(path)

    def make_task(self):
        mode = self.mode_combo.currentText()
        in_path = self.in_path_edit.text().strip()
        out_path = self.out_path_edit.text().strip()
        message = self.message_edit.toPlainText()

        if not in_path or not os.path.isfile(in_path):
            raise ValueError("select a valid source PNG file")
        if mode == "Embed message" and not out_path:
            raise ValueError("choose an output path")
        if mode == "Embed message" and not message:
            raise ValueError("enter a message to embed")

        def task(emit, is_cancelled):
            if mode == "Embed message":
                emit(f"embedding {len(message.encode('utf-8'))} byte message into {in_path}...", "meta")
                try:
                    n = embed_message(in_path, message, out_path)
                except Exception as exc:
                    emit(f"embed failed: {exc}", "error")
                    return
                emit(f"wrote {n} bytes into {out_path}", "success")
                emit("stego image saved", "cyan")
            else:
                emit(f"scanning {in_path} for a hidden payload...", "meta")
                try:
                    msg = extract_message(in_path)
                except Exception as exc:
                    emit(f"extract failed: {exc}", "error")
                    return
                emit("extracted message:", "cyan")
                for line in msg.splitlines() or [""]:
                    emit(f"  {line}", "success")

        return task
