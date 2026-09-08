"""TCP connect-scan module: authorized recon of hosts you control."""
from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QLineEdit, QSpinBox, QWidget,
)

from jegeo.modules.base import BaseModule

COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 465, 587,
    993, 995, 1723, 3306, 3389, 5432, 5900, 6379, 8000, 8080, 8443, 9200,
    27017,
]

WELL_KNOWN = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP",
    110: "POP3", 111: "RPCBIND", 135: "MSRPC", 139: "NetBIOS", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 465: "SMTPS", 587: "SMTP-SUB", 993: "IMAPS",
    995: "POP3S", 1723: "PPTP", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    5900: "VNC", 6379: "Redis", 8000: "HTTP-ALT", 8080: "HTTP-PROXY",
    8443: "HTTPS-ALT", 9200: "Elasticsearch", 27017: "MongoDB",
}


def parse_ports(spec: str) -> list[int]:
    spec = spec.strip().lower()
    if spec in ("", "common"):
        return list(COMMON_PORTS)
    ports: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            lo, hi = int(a), int(b)
            if lo > hi:
                lo, hi = hi, lo
            ports.update(range(max(lo, 1), min(hi, 65535) + 1))
        else:
            ports.add(int(part))
    return sorted(ports)


def scan_one(host: str, port: int, timeout: float) -> tuple[int, bool]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        return port, result == 0
    except OSError:
        return port, False
    finally:
        sock.close()


class NetworkScannerModule(BaseModule):
    display_name = "Network Scanner"
    glyph = "⌁"
    tagline = "TCP host & port discovery"
    notice = "Only scan hosts and networks you own or are explicitly authorized to test."

    def build_controls(self) -> QWidget:
        form = QFormLayout()
        form.setSpacing(8)

        self.host_input = QLineEdit("127.0.0.1")
        self.host_input.setPlaceholderText("hostname or IP, e.g. 192.168.1.10")
        form.addRow("TARGET", self.host_input)

        self.port_input = QLineEdit("common")
        self.port_input.setPlaceholderText("common | 22,80,443 | 1-1024")
        form.addRow("PORTS", self.port_input)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(50, 3000)
        self.timeout_spin.setValue(400)
        self.timeout_spin.setSuffix(" ms")
        form.addRow("TIMEOUT", self.timeout_spin)

        self.workers_combo = QComboBox()
        self.workers_combo.addItems(["25", "50", "100", "200"])
        self.workers_combo.setCurrentText("100")
        form.addRow("CONCURRENCY", self.workers_combo)

        wrapper = QWidget()
        wrapper.setLayout(form)
        return wrapper

    def make_task(self):
        host = self.host_input.text().strip() or "127.0.0.1"
        ports = parse_ports(self.port_input.text())
        timeout = self.timeout_spin.value() / 1000.0
        max_workers = int(self.workers_combo.currentText())

        if not ports:
            raise ValueError("no ports parsed from spec")
        if len(ports) > 20000:
            raise ValueError("port range too large (max 20000 per run)")

        def task(emit, is_cancelled):
            try:
                resolved = socket.gethostbyname(host)
            except socket.gaierror as exc:
                emit(f"could not resolve '{host}': {exc}", "error")
                return
            emit(f"target resolved: {host} -> {resolved}", "meta")
            emit(f"scanning {len(ports)} port(s) with {max_workers} workers...", "meta")

            open_ports = []
            scanned = 0
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {
                    pool.submit(scan_one, resolved, p, timeout): p for p in ports
                }
                for fut in as_completed(futures):
                    if is_cancelled():
                        for f in futures:
                            f.cancel()
                        emit("scan aborted by operator", "warn")
                        return
                    port, is_open = fut.result()
                    scanned += 1
                    if is_open:
                        svc = WELL_KNOWN.get(port, "unknown")
                        open_ports.append(port)
                        emit(f"  [OPEN]  {port:>5}/tcp  {svc}", "success")
                    if scanned % 500 == 0:
                        emit(f"  ... {scanned}/{len(ports)} probed", "meta")

            emit(f"scan finished: {len(open_ports)} open / {len(ports)} probed", "cyan")
            if open_ports:
                emit(f"open ports: {', '.join(str(p) for p in sorted(open_ports))}", "info")
            else:
                emit("no open ports found in range", "info")

        return task
