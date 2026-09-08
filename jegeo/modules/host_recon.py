"""Passive host intel: DNS resolution, reverse DNS, whois, traceroute."""
from __future__ import annotations

import shutil
import socket
import subprocess

from PySide6.QtWidgets import (
    QCheckBox, QFormLayout, QLineEdit, QVBoxLayout, QWidget,
)

from jegeo.modules.base import BaseModule


class HostReconModule(BaseModule):
    display_name = "Host Recon"
    glyph = "◎"
    tagline = "DNS / reverse DNS / whois / traceroute"
    notice = "Passive/public-record lookups only — respect target scope and local law."

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(0, 0, 0, 0)

        form = QFormLayout()
        self.target_input = QLineEdit("example.com")
        self.target_input.setPlaceholderText("domain or IP")
        form.addRow("TARGET", self.target_input)
        outer.addLayout(form)

        self.chk_dns = QCheckBox("Forward DNS resolution")
        self.chk_dns.setChecked(True)
        self.chk_rdns = QCheckBox("Reverse DNS (PTR)")
        self.chk_rdns.setChecked(True)
        self.chk_whois = QCheckBox("WHOIS record (requires 'whois' binary)")
        self.chk_whois.setChecked(True)
        self.chk_trace = QCheckBox("Traceroute (requires 'traceroute'/'tracepath')")
        self.chk_trace.setChecked(False)
        for c in (self.chk_dns, self.chk_rdns, self.chk_whois, self.chk_trace):
            outer.addWidget(c)

        return wrapper

    def make_task(self):
        target = self.target_input.text().strip()
        if not target:
            raise ValueError("target is required")
        do_dns = self.chk_dns.isChecked()
        do_rdns = self.chk_rdns.isChecked()
        do_whois = self.chk_whois.isChecked()
        do_trace = self.chk_trace.isChecked()

        def task(emit, is_cancelled):
            resolved_ip = None

            if do_dns:
                emit("resolving forward DNS...", "meta")
                try:
                    infos = socket.getaddrinfo(target, None)
                    addrs = sorted({info[4][0] for info in infos})
                    resolved_ip = addrs[0]
                    for a in addrs:
                        emit(f"  A/AAAA  {a}", "success")
                except socket.gaierror as exc:
                    emit(f"  DNS resolution failed: {exc}", "error")

            if is_cancelled():
                return

            if do_rdns:
                emit("resolving reverse DNS (PTR)...", "meta")
                ip_to_check = resolved_ip or target
                try:
                    host, _, _ = socket.gethostbyaddr(ip_to_check)
                    emit(f"  PTR  {ip_to_check} -> {host}", "success")
                except (socket.herror, socket.gaierror) as exc:
                    emit(f"  no PTR record ({exc})", "warn")

            if is_cancelled():
                return

            if do_whois:
                emit("querying WHOIS...", "meta")
                binpath = shutil.which("whois")
                if not binpath:
                    emit("  'whois' not installed — try: sudo dnf install whois", "warn")
                else:
                    try:
                        proc = subprocess.run(
                            [binpath, target], capture_output=True, text=True,
                            timeout=15,
                        )
                        lines = [
                            ln for ln in proc.stdout.splitlines()
                            if ln.strip() and not ln.strip().startswith("%")
                        ]
                        for ln in lines[:40]:
                            emit(f"  {ln}", "info")
                        if len(lines) > 40:
                            emit(f"  ... ({len(lines) - 40} more lines truncated)", "meta")
                    except subprocess.TimeoutExpired:
                        emit("  whois query timed out", "error")
                    except OSError as exc:
                        emit(f"  whois failed: {exc}", "error")

            if is_cancelled():
                return

            if do_trace:
                emit("tracing route...", "meta")
                cmd = None
                for candidate in ("traceroute", "tracepath"):
                    p = shutil.which(candidate)
                    if p:
                        cmd = [p, target]
                        break
                if not cmd:
                    emit(
                        "  no traceroute/tracepath installed — try: "
                        "sudo dnf install traceroute", "warn",
                    )
                else:
                    try:
                        proc = subprocess.Popen(
                            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1,
                        )
                        for line in proc.stdout:
                            if is_cancelled():
                                proc.terminate()
                                emit("  traceroute aborted", "warn")
                                break
                            emit(f"  {line.rstrip()}", "info")
                        proc.wait(timeout=30)
                    except (OSError, subprocess.TimeoutExpired) as exc:
                        emit(f"  traceroute failed: {exc}", "error")

            emit("host recon complete", "cyan")

        return task
