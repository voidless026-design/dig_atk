"""Decorative HUD chrome: corner brackets + a slow scanline sweep.

Purely cosmetic — sits above the real UI, ignores all mouse/keyboard input,
and repaints itself on a timer to keep the "operator console" feel alive
without interfering with any widget underneath it.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class HudOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._sweep = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def _tick(self):
        self._sweep += 0.0035
        if self._sweep > 1.0:
            self._sweep = 0.0
        self.update()

    def paintEvent(self, event):  # noqa: N802 (Qt override)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # corner brackets
        pen = QPen(QColor(40, 245, 232, 130))
        pen.setWidth(2)
        p.setPen(pen)
        length = 22
        margin = 6
        corners = [
            ((margin, margin), (1, 0), (0, 1)),
            ((w - margin, margin), (-1, 0), (0, 1)),
            ((margin, h - margin), (1, 0), (0, -1)),
            ((w - margin, h - margin), (-1, 0), (0, -1)),
        ]
        for (x, y), dx, dy in corners:
            p.drawLine(x, y, x + dx[0] * length, y + dx[1] * length)
            p.drawLine(x, y, x + dy[0] * length, y + dy[1] * length)

        # slow horizontal scan sweep
        sweep_y = self._sweep * h
        grad_h = 90
        pen2 = QPen(Qt.PenStyle.NoPen)
        p.setPen(pen2)
        p.setOpacity(0.05)
        p.setBrush(QColor(40, 245, 232))
        p.drawRect(QRectF(0, sweep_y - grad_h, w, grad_h))
        p.setOpacity(1.0)

        p.end()
