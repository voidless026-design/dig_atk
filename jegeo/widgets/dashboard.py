"""Main operator console: sidebar of modules + a stacked panel on the right."""
from __future__ import annotations

import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QScrollArea,
    QStackedWidget, QVBoxLayout, QWidget,
)

from jegeo.widgets.module_button import ModuleButton


class Dashboard(QWidget):
    def __init__(self, module_classes, parent=None):
        super().__init__(parent)
        self._modules = {}
        self._panels = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar(module_classes), stretch=0)

        self.stack = QStackedWidget()
        for cls in module_classes:
            panel = cls()
            self._panels[cls.__name__] = panel
            self.stack.addWidget(panel)
        body.addWidget(self.stack, stretch=1)

        body_widget = QWidget()
        body_widget.setLayout(body)
        root.addWidget(body_widget, stretch=1)

        if module_classes:
            first = module_classes[0]
            self._buttons[first.__name__].setChecked(True)
            self.stack.setCurrentWidget(self._panels[first.__name__])

    # ------------------------------------------------------------------
    def _build_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setProperty("role", "panel")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)

        title = QLabel("JEGEO PAYLOAD")
        title.setProperty("role", "title")
        subtitle = QLabel("OPERATOR CONSOLE")
        subtitle.setProperty("role", "subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)
        layout.addStretch(1)

        self.clock_lbl = QLabel()
        self.clock_lbl.setStyleSheet(
            "color: #28f5e8; font-size: 13px; letter-spacing: 2px;"
        )
        layout.addWidget(self.clock_lbl)

        timer = QTimer(self)
        timer.timeout.connect(self._tick_clock)
        timer.start(1000)
        self._tick_clock()

        return bar

    def _tick_clock(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.clock_lbl.setText(f"⏱ {now}   ●  LINK ACTIVE")

    def _build_sidebar(self, module_classes) -> QWidget:
        container = QFrame()
        container.setProperty("role", "panel")
        container.setFixedWidth(240)
        outer = QVBoxLayout(container)
        outer.setContentsMargins(10, 14, 10, 14)
        outer.setSpacing(6)

        label = QLabel("MODULES")
        label.setProperty("role", "section")
        outer.addWidget(label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(6)

        self._buttons = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for cls in module_classes:
            btn = ModuleButton(cls.glyph, cls.display_name, cls.tagline)
            btn.clicked.connect(lambda _checked, k=cls.__name__: self._select(k))
            self._group.addButton(btn)
            self._buttons[cls.__name__] = btn
            inner_layout.addWidget(btn)

        inner_layout.addStretch(1)
        scroll.setWidget(inner)
        outer.addWidget(scroll, stretch=1)
        return container

    def _select(self, key: str):
        self.stack.setCurrentWidget(self._panels[key])

    def shutdown(self):
        """Cancel and join any module task still running before the app exits."""
        for panel in self._panels.values():
            runner = getattr(panel, "_runner", None)
            if runner is not None and runner.running:
                runner.cancel()
                thread = runner._thread
                if thread is not None:
                    thread.quit()
                    thread.wait(3000)
