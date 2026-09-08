"""Sidebar entry for one module: a checkable button styled as a HUD tab."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class ModuleButton(QPushButton):
    def __init__(self, glyph: str, name: str, tagline: str, parent=None):
        super().__init__(f"{glyph}   {name}", parent)
        self.setProperty("role", "module")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tagline)
        self.setMinimumHeight(38)
