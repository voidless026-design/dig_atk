"""Background task execution so long-running recon never freezes the UI.

Every module hands a plain function of the shape ``task(emit, is_cancelled)``
to :class:`TaskRunner`, which moves it onto a QThread and relays ``emit()``
calls back to the GUI thread as Qt signals.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal


class _Worker(QObject):
    line = Signal(str, str)  # text, level
    finished = Signal(bool, str)  # ok, error_message

    def __init__(self, task: Callable):
        super().__init__()
        self._task = task
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled

    def run(self):
        ok, err = True, ""
        try:
            self._task(self._emit, self.is_cancelled)
        except Exception as exc:  # surfaced to the console, not swallowed
            ok, err = False, str(exc)
        self.finished.emit(ok, err)

    def _emit(self, text: str, level: str = "info"):
        self.line.emit(text, level)


class TaskRunner(QObject):
    """Owns the QThread lifecycle for one in-flight module task."""

    line = Signal(str, str)
    finished = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _Worker | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def start(self, task: Callable):
        if self.running:
            return
        self._thread = QThread(self)
        self._worker = _Worker(task)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.line.connect(self.line.emit)
        self._worker.finished.connect(self._on_finished)

        self._thread.start()

    def cancel(self):
        if self._worker is not None:
            self._worker.cancel()

    def _on_finished(self, ok: bool, err: str):
        self.finished.emit(ok, err)
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
        self._thread = None
        self._worker = None
