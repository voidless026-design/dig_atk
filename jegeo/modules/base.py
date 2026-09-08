"""Common chrome shared by every JEGEO PAYLOAD module.

Each module is a self-contained "operation": a header, a control strip the
module defines itself, an EXECUTE / ABORT button pair, and a console it
streams results into. Subclasses only implement ``build_controls()`` (the
inputs) and ``make_task()`` (the actual work, run off the GUI thread).
"""
from __future__ import annotations

import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)

from jegeo.core.worker import TaskRunner
from jegeo.widgets.terminal_output import TerminalOutput


class BaseModule(QWidget):
    display_name: str = "Module"
    glyph: str = "✦"
    tagline: str = ""
    notice: str = ""  # optional ethics/scope reminder shown under the header

    def __init__(self, parent=None):
        super().__init__(parent)
        self._runner = TaskRunner(self)
        self._runner.line.connect(self._on_line)
        self._runner.finished.connect(self._on_finished)
        self._build_chrome()

    # ---- overridden by subclasses -----------------------------------
    def build_controls(self) -> QWidget:
        raise NotImplementedError

    def make_task(self):
        """Return a callable ``task(emit, is_cancelled)`` to run in the background."""
        raise NotImplementedError

    # ---- shared chrome -------------------------------------------------
    def _build_chrome(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        glyph_lbl = QLabel(self.glyph)
        glyph_lbl.setStyleSheet("color: #28f5e8; font-size: 22px;")
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        name_lbl = QLabel(self.display_name.upper())
        name_lbl.setProperty("role", "title")
        name_lbl.setStyleSheet("font-size: 15px; letter-spacing: 3px; color: #28f5e8;")
        tag_lbl = QLabel(self.tagline)
        tag_lbl.setProperty("role", "tagline")
        title_box.addWidget(name_lbl)
        title_box.addWidget(tag_lbl)
        header.addWidget(glyph_lbl)
        header.addSpacing(8)
        header.addLayout(title_box)
        header.addStretch(1)
        root.addLayout(header)

        if self.notice:
            notice_lbl = QLabel(f"⚠ {self.notice}")
            notice_lbl.setWordWrap(True)
            notice_lbl.setStyleSheet(
                "color: #ffb347; font-size: 10px; letter-spacing: 1px; "
                "border: 1px solid #4a3413; background-color: #1a1408; "
                "padding: 5px 8px; border-radius: 2px;"
            )
            root.addWidget(notice_lbl)

        rule = QFrame()
        rule.setProperty("role", "hairline")
        rule.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(rule)

        controls_panel = QFrame()
        controls_panel.setProperty("role", "panel")
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(14, 12, 14, 12)
        controls_layout.addWidget(self.build_controls())
        root.addWidget(controls_panel)

        action_row = QHBoxLayout()
        self.execute_btn = _ActionButton("▸ EXECUTE")
        self.execute_btn.clicked.connect(self._execute)
        self.abort_btn = _ActionButton("■ ABORT")
        self.abort_btn.setProperty("role", "danger")
        self.abort_btn.setEnabled(False)
        self.abort_btn.clicked.connect(self._abort)
        self.export_btn = _ActionButton("⇩ EXPORT")
        self.export_btn.clicked.connect(self._export)
        self.status_lbl = QLabel("STANDBY")
        self.status_lbl.setStyleSheet("color: #5f8b90; letter-spacing: 2px; font-size: 11px;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        action_row.addWidget(self.execute_btn)
        action_row.addWidget(self.abort_btn)
        action_row.addWidget(self.export_btn)
        action_row.addStretch(1)
        action_row.addWidget(self.status_lbl)
        root.addLayout(action_row)

        console_lbl = QLabel("OUTPUT STREAM")
        console_lbl.setProperty("role", "section")
        root.addWidget(console_lbl)

        self.console = TerminalOutput()
        self.console.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self.console, stretch=1)

    # ---- execution plumbing --------------------------------------------
    def _execute(self):
        if self._runner.running:
            return
        self.console.clear()
        self.console.append_line(f"$ initiating {self.display_name.lower()}...", "meta")
        self.execute_btn.setEnabled(False)
        self.abort_btn.setEnabled(True)
        self.status_lbl.setText("RUNNING")
        self.status_lbl.setStyleSheet("color: #28f5e8; letter-spacing: 2px; font-size: 11px;")
        try:
            task = self.make_task()
        except Exception as exc:
            self.console.append_line(f"CONFIG ERROR: {exc}", "error")
            self._reset_buttons(ok=False)
            return
        self._runner.start(task)

    def _abort(self):
        self._runner.cancel()
        self.console.append_line("abort signal sent...", "warn")
        self.status_lbl.setText("ABORTING")

    def _on_line(self, text: str, level: str):
        self.console.append_line(text, level)

    def _on_finished(self, ok: bool, err: str):
        if err:
            self.console.append_line(f"ERROR: {err}", "error")
        self.console.append_line(
            "-- complete --" if ok else "-- terminated --",
            "success" if ok else "warn",
        )
        self._reset_buttons(ok)

    def _reset_buttons(self, ok: bool):
        self.execute_btn.setEnabled(True)
        self.abort_btn.setEnabled(False)
        self.status_lbl.setText("STANDBY")
        self.status_lbl.setStyleSheet("color: #5f8b90; letter-spacing: 2px; font-size: 11px;")

    def _export(self):
        text = self.console.toPlainText()
        if not text.strip():
            self.console.append_line("nothing to export yet — run the module first", "warn")
            return
        slug = self.display_name.lower().replace(" ", "_").replace("/", "-")
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"jegeo_{slug}_{ts}.log"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export output", default_name, "Log files (*.log *.txt);;All files (*)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as exc:
            self.console.append_line(f"export failed: {exc}", "error")
            return
        self.console.append_line(f"exported to {path}", "success")


class _ActionButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(120)
