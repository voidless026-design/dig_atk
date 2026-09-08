"""A read-only, color-coded console used by every module to stream results."""
from __future__ import annotations

import datetime

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

_LEVEL_COLORS = {
    "info": "#9fe8e3",
    "meta": "#5f8b90",
    "warn": "#ffb347",
    "error": "#ff3355",
    "success": "#5dffa0",
    "cyan": "#28f5e8",
}


class TerminalOutput(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("consoleOutput")
        self.setReadOnly(True)
        self.setMaximumBlockCount(4000)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

    def append_line(self, text: str, level: str = "info"):
        color = _LEVEL_COLORS.get(level, _LEVEL_COLORS["info"])
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        safe = (
            text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        html = (
            f'<span style="color:#33555a">[{ts}]</span> '
            f'<span style="color:{color}">{safe}</span>'
        )
        self.appendHtml(html)
        self.moveCursor(QTextCursor.MoveOperation.End)

    def append_raw(self, text: str, level: str = "info"):
        for line in text.splitlines() or [""]:
            self.append_line(line, level)
