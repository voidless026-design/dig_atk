"""Full-window boot sequence shown before the dashboard loads.

Scrolls a fake system-init log with a typewriter effect, fills a progress
bar, then emits ``booted`` so the main window can swap to the dashboard.
Purely cosmetic — no real system calls happen here.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from jegeo.widgets.terminal_output import TerminalOutput

BOOT_LOG = [
    "jegeo-core: cold start",
    "loading operator profile...",
    "mounting toolchain volumes [network] [crypto] [recon] [audio]",
    "calibrating hologram projector array",
    "handshaking with local interface adapters",
    "verifying module signatures... OK",
    "spinning up sandboxed execution threads",
    "syncing HUD overlay clock",
    "authorization scope: LOCAL / OWNED SYSTEMS ONLY",
    "operator console ready",
]


class BootScreen(QWidget):
    booted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(14)
        layout.addStretch(2)

        rule_top = QLabel("//////////////////////////////////////////////////")
        rule_top.setStyleSheet("color: #123339; font-size: 11px;")
        layout.addWidget(rule_top)

        logo_lbl = QLabel("JEGEO PAYLOAD")
        logo_lbl.setStyleSheet(
            "color: #28f5e8; font-size: 42px; font-weight: 700; letter-spacing: 10px;"
        )
        layout.addWidget(logo_lbl)

        subtitle_lbl = QLabel("O P E R A T O R   C O N S O L E")
        subtitle_lbl.setStyleSheet(
            "color: #5f8b90; font-size: 13px; letter-spacing: 4px;"
        )
        layout.addWidget(subtitle_lbl)

        rule_bottom = QLabel("//////////////////////////////////////////////////")
        rule_bottom.setStyleSheet("color: #123339; font-size: 11px;")
        layout.addWidget(rule_bottom)
        layout.addSpacing(8)

        self.log = TerminalOutput()
        self.log.setFixedHeight(180)
        layout.addWidget(self.log)

        self.progress = QProgressBar()
        self.progress.setRange(0, len(BOOT_LOG))
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        layout.addWidget(self.progress)

        self.status_lbl = QLabel("INITIALIZING...")
        self.status_lbl.setStyleSheet(
            "color: #5f8b90; letter-spacing: 3px; font-size: 11px;"
        )
        layout.addWidget(self.status_lbl)
        layout.addStretch(3)

        self._i = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)

    def start(self):
        self._i = 0
        self.log.clear()
        self.progress.setValue(0)
        self._timer.start(220)

    def _advance(self):
        if self._i >= len(BOOT_LOG):
            self._timer.stop()
            self.status_lbl.setText("ACCESS GRANTED")
            self.status_lbl.setStyleSheet(
                "color: #5dffa0; letter-spacing: 3px; font-size: 11px;"
            )
            QTimer.singleShot(500, self.booted.emit)
            return
        self.log.append_line(BOOT_LOG[self._i], "cyan")
        self._i += 1
        self.progress.setValue(self._i)
