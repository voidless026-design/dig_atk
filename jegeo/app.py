"""Main window: boots into an animated splash, then swaps to the dashboard."""
from __future__ import annotations

import sys

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from jegeo import theme
from jegeo.modules.crypto_toolkit import CryptoToolkitModule
from jegeo.modules.hash_id import HashIdModule
from jegeo.modules.host_recon import HostReconModule
from jegeo.modules.network_scanner import NetworkScannerModule
from jegeo.modules.password_audit import PasswordAuditModule
from jegeo.modules.steg_tool import StegToolModule
from jegeo.modules.sys_recon import SysReconModule
from jegeo.modules.wifi_recon import WifiReconModule
from jegeo.widgets.boot_screen import BootScreen
from jegeo.widgets.dashboard import Dashboard
from jegeo.widgets.hud_overlay import HudOverlay

MODULE_CLASSES = [
    NetworkScannerModule,
    HostReconModule,
    WifiReconModule,
    SysReconModule,
    CryptoToolkitModule,
    HashIdModule,
    PasswordAuditModule,
    StegToolModule,
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("rootWindow")
        self.setWindowTitle("JEGEO PAYLOAD — Operator Console")
        self.resize(QSize(1180, 760))
        self.setMinimumSize(QSize(900, 600))

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.boot_screen = BootScreen()
        self.boot_screen.booted.connect(self._show_dashboard)
        self.stack.addWidget(self.boot_screen)

        self.dashboard = None  # built lazily after boot for a snappier launch

        self.hud = HudOverlay(self)
        self.hud.setGeometry(self.rect())
        self.hud.raise_()

        self.boot_screen.start()

    def _show_dashboard(self):
        self.dashboard = Dashboard(MODULE_CLASSES)
        self.stack.addWidget(self.dashboard)
        self.stack.setCurrentWidget(self.dashboard)
        self.hud.raise_()

    def resizeEvent(self, event):  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        self.hud.setGeometry(self.rect())

    def closeEvent(self, event):  # noqa: N802 (Qt override)
        if self.dashboard is not None:
            self.dashboard.shutdown()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("JEGEO PAYLOAD")
    app.setStyleSheet(theme.stylesheet())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
