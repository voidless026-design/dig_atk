# JEGEO PAYLOAD — Operator Console

A homemade, Rainbow Six Siege *Dokkaebi*-inspired hacking-device GUI for
Linux. It doesn't attempt to be an operating system — it's a fully
functional desktop app that gives you that hologram/terminal "operator
console" immersion, wrapped around a set of real, defensive/educational
security tools instead of the character's fictional gadget effects.

Built with Python + [PySide6](https://doc.qt.io/qtforpython/) (Qt for
Python). Tested on Fedora Workstation; should run on any modern Linux
desktop.

![status](https://img.shields.io/badge/status-active-28f5e8)

## What's inside

A boot sequence, a HUD-styled dashboard, and eight modules:

| Module | What it does |
|---|---|
| **Network Scanner** | Threaded TCP connect-scan of a host — common ports or a custom range/list. |
| **Host Recon** | Forward/reverse DNS, WHOIS, and traceroute for a domain or IP. |
| **Wi-Fi Recon** | Lists visible Wi-Fi networks and current link status via `nmcli` (read-only, no association or deauth). |
| **Rig Status** | Local machine telemetry — CPU, memory, disks, network interfaces, uptime. |
| **Crypto Toolkit** | Base64 / hex / ROT13 / XOR, plus password-based AES-256-GCM encrypt/decrypt. |
| **Hash ID / Digest** | Generate digests (MD5/SHA-family/BLAKE2), fingerprint an unknown hash's likely format, or check it against a small built-in common-password sample. |
| **Password Audit** | Fully offline entropy/pattern analysis and illustrative crack-time estimates for a password you type in. |
| **Steganography** | Hide or reveal a text message inside a PNG using LSB steganography. |

Every module streams its output into a color-coded console with the same
"operator console" feel as the boot sequence, and every scan/lookup runs on
a background thread so the UI never locks up — with a working **ABORT**
button.

## Ethics / scope

These are legitimate, dual-use security and networking utilities — the
kind you'd find in any pentesting distro — presented through an immersive
UI, **not** exploit tooling. Only point the Network Scanner, Host Recon, or
Wi-Fi Recon modules at systems and networks **you own or are explicitly
authorized to test.** The Hash ID and Password Audit modules ship with a
small (a few hundred entries) hand-written sample of common passwords for
demonstrating *why* weak secrets are weak — it is not a real
credential-cracking wordlist.

## Install (Fedora)

```bash
git clone <this-repo-url>
cd dig_atk
./scripts/install-fedora.sh
source .venv/bin/activate
jegeo
```

The install script installs `whois`, `traceroute`, and NetworkManager
(usually already present on Fedora Workstation) via `dnf`, then creates a
`.venv` and installs the Python dependencies from `requirements.txt`.

`nmcli` (Wi-Fi Recon), `whois`, and `traceroute`/`tracepath` are optional —
if any of them isn't installed, that specific check is skipped with a
message telling you what to install, instead of crashing the module.

### Manual install (any distro)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m jegeo
```

## Project layout

```
jegeo/
  app.py                  # QApplication entrypoint, main window, boot -> dashboard
  theme.py                # color palette + QSS stylesheet
  core/
    worker.py             # QThread task runner (keeps the UI responsive)
    wordlist.py           # small sample common-password list
  widgets/
    boot_screen.py         # animated startup sequence
    hud_overlay.py          # corner brackets + scanline sweep
    dashboard.py            # sidebar + module switcher
    module_button.py        # sidebar entry
    terminal_output.py      # color-coded console widget
  modules/
    base.py                 # shared module chrome (header, controls, console, execute/abort)
    network_scanner.py
    host_recon.py
    wifi_recon.py
    sys_recon.py
    crypto_toolkit.py
    hash_id.py
    password_audit.py
    steg_tool.py
scripts/install-fedora.sh
```

## Adding a new module

Subclass `jegeo.modules.base.BaseModule`, implement `build_controls()`
(your input widgets) and `make_task()` (returns a `task(emit, is_cancelled)`
callable that does the work off the GUI thread, calling `emit(text, level)`
to stream output — levels are `info`, `meta`, `warn`, `error`, `success`,
`cyan`), then add the class to `MODULE_CLASSES` in `jegeo/app.py`.

## License

MIT. This is a fan-inspired, original implementation — no assets, code, or
branding from Ubisoft or Rainbow Six Siege are included.
