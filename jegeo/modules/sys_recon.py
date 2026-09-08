"""Local machine ('operator rig') status — CPU, memory, disk, interfaces."""
from __future__ import annotations

import datetime
import platform
import socket

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from jegeo.modules.base import BaseModule


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} PB"


class SysReconModule(BaseModule):
    display_name = "Rig Status"
    glyph = "▣"
    tagline = "Local system telemetry"

    def build_controls(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(
            "Reads telemetry for THIS machine only — CPU load, memory, disks, "
            "network interfaces, uptime."
        )
        label.setWordWrap(True)
        label.setStyleSheet("color: #5f8b90; font-size: 11px;")
        layout.addWidget(label)
        return wrapper

    def make_task(self):
        def task(emit, is_cancelled):
            uname = platform.uname()
            emit("== SYSTEM ==", "cyan")
            emit(f"  hostname:  {socket.gethostname()}", "info")
            emit(f"  os:        {uname.system} {uname.release}", "info")
            emit(f"  version:   {uname.version}", "meta")
            emit(f"  arch:      {uname.machine}", "info")
            emit(f"  python:    {platform.python_version()}", "meta")

            if is_cancelled():
                return

            if psutil is not None:
                emit("== CPU / MEMORY ==", "cyan")
                pct = psutil.cpu_percent(interval=0.3)
                emit(f"  cpu cores:   {psutil.cpu_count(logical=False)} physical / {psutil.cpu_count()} logical", "info")
                emit(f"  cpu load:    {pct:.1f}%", "info")
                vm = psutil.virtual_memory()
                emit(f"  memory:      {_fmt_bytes(vm.used)} / {_fmt_bytes(vm.total)} ({vm.percent}%)", "info")
                sw = psutil.swap_memory()
                if sw.total:
                    emit(f"  swap:        {_fmt_bytes(sw.used)} / {_fmt_bytes(sw.total)} ({sw.percent}%)", "meta")

                if is_cancelled():
                    return

                emit("== DISKS ==", "cyan")
                for part in psutil.disk_partitions(all=False):
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                    except (PermissionError, OSError):
                        continue
                    emit(
                        f"  {part.mountpoint:<20} {_fmt_bytes(usage.used)} / "
                        f"{_fmt_bytes(usage.total)} ({usage.percent}%)", "info",
                    )

                if is_cancelled():
                    return

                emit("== NETWORK INTERFACES ==", "cyan")
                addrs = psutil.net_if_addrs()
                stats = psutil.net_if_stats()
                for name, addr_list in addrs.items():
                    is_up = stats[name].isup if name in stats else False
                    emit(f"  {name} [{'UP' if is_up else 'DOWN'}]", "success" if is_up else "meta")
                    for a in addr_list:
                        if a.family.name in ("AF_INET", "AF_INET6"):
                            emit(f"    {a.family.name}: {a.address}", "info")

                boot_ts = psutil.boot_time()
                uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_ts)
                emit(f"== UPTIME: {str(uptime).split('.')[0]} ==", "cyan")
            else:
                emit(
                    "psutil not installed — install it for CPU/memory/disk/"
                    "network detail (pip install psutil)", "warn",
                )

            emit("rig status snapshot complete", "success")

        return task
