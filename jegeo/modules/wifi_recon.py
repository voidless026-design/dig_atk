"""Wi-Fi environment recon via NetworkManager's `nmcli` (read-only, passive)."""
from __future__ import annotations

import shutil
import subprocess

from PySide6.QtWidgets import QCheckBox, QVBoxLayout, QWidget

from jegeo.modules.base import BaseModule


def _run(cmd: list[str], timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


class WifiReconModule(BaseModule):
    display_name = "Wi-Fi Recon"
    glyph = "◈"
    tagline = "Visible networks & link status (nmcli)"
    notice = "Read-only survey of your own adapter's view — no association, no deauth."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        self.chk_rescan = QCheckBox("Force a fresh scan before listing (may take a few seconds)")
        self.chk_rescan.setChecked(True)
        layout.addWidget(self.chk_rescan)
        return wrapper

    def make_task(self):
        do_rescan = self.chk_rescan.isChecked()

        def task(emit, is_cancelled):
            nmcli = shutil.which("nmcli")
            if not nmcli:
                emit(
                    "'nmcli' not found — NetworkManager is required "
                    "(it ships by default on Fedora Workstation).", "error",
                )
                return

            emit("checking radio & connection status...", "meta")
            try:
                status = _run([nmcli, "-t", "-f", "WIFI", "radio"])
                radio_state = status.stdout.strip() or "unknown"
                emit(f"  wifi radio: {radio_state}", "info")
            except (OSError, subprocess.TimeoutExpired) as exc:
                emit(f"  could not read radio state: {exc}", "warn")

            try:
                active = _run(
                    [nmcli, "-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY", "dev", "wifi"]
                )
                for line in active.stdout.splitlines():
                    parts = line.split(":")
                    if len(parts) >= 2 and parts[0] == "yes":
                        ssid = parts[1] or "<hidden>"
                        emit(f"  connected to: {ssid}", "success")
                        break
                else:
                    emit("  not currently associated to a Wi-Fi network", "info")
            except (OSError, subprocess.TimeoutExpired) as exc:
                emit(f"  could not read active connection: {exc}", "warn")

            if is_cancelled():
                return

            if do_rescan:
                emit("requesting rescan...", "meta")
                try:
                    _run([nmcli, "dev", "wifi", "rescan"], timeout=10)
                except (OSError, subprocess.TimeoutExpired):
                    emit("  rescan request ignored/unsupported, listing cached results", "warn")

            if is_cancelled():
                return

            emit("enumerating visible access points...", "meta")
            try:
                res = _run(
                    [nmcli, "-t", "-f", "SSID,BSSID,CHAN,SIGNAL,SECURITY", "dev", "wifi", "list"]
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                emit(f"  scan failed: {exc}", "error")
                return

            rows = []
            for line in res.stdout.splitlines():
                # BSSID contains escaped colons ("\:"); nmcli's -t mode escapes
                # separators inside a field, so split on unescaped colons only.
                fields, buf, esc = [], "", False
                for ch in line:
                    if esc:
                        buf += ch
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == ":":
                        fields.append(buf)
                        buf = ""
                    else:
                        buf += ch
                fields.append(buf)
                if len(fields) >= 5:
                    rows.append(fields[:5])

            if not rows:
                emit("  no networks found (adapter may be disabled or unsupported)", "warn")
                return

            rows.sort(key=lambda r: int(r[3]) if r[3].isdigit() else 0, reverse=True)
            emit(f"  {len(rows)} network(s) visible:", "info")
            emit(f"  {'SSID':<24} {'CHAN':<5} {'SIG':<4} SECURITY", "meta")
            for ssid, bssid, chan, signal, security in rows:
                name = ssid if ssid else "<hidden>"
                sec = security if security else "OPEN"
                emit(f"  {name:<24} {chan:<5} {signal:<4} {sec}", "success")

            emit("wifi recon complete", "cyan")

        return task
