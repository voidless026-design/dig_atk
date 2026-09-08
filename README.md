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

A boot sequence, a HUD-styled dashboard, and twelve modules — the local
tools below run entirely offline against your own machine, network, or
files; everything under **Online Intelligence** talks to a public API
over the internet. Every module can also **EXPORT** its console output
to a timestamped log file.

| Module | What it does |
|---|---|
| **Network Scanner** | Threaded TCP connect-scan of a host — common ports or a custom range/list. |
| **Host Recon** | Forward/reverse DNS, WHOIS, and traceroute for a domain or IP, via local system tools. |
| **Wi-Fi Recon** | Lists visible Wi-Fi networks and current link status via `nmcli` (read-only, no association or deauth). |
| **Rig Status** | Local machine telemetry — CPU, memory, disks, network interfaces, uptime. |
| **Crypto Toolkit** | Base64 / hex / ROT13 / XOR, plus password-based AES-256-GCM encrypt/decrypt. |
| **Hash ID / Digest** | Generate digests (MD5/SHA-family/BLAKE2), fingerprint an unknown hash's likely format, or check it against a small built-in common-password sample. |
| **Password Audit** | Fully offline entropy/pattern analysis and illustrative crack-time estimates for a password you type in. |
| **Steganography** | Hide or reveal a text message inside a PNG using LSB steganography. |

### Online Intelligence (OSINT)

These reach out to the internet — see [Ethics / scope](#ethics--scope)
below before pointing them at anything.

| Module | What it does |
|---|---|
| **OSINT Intel** | Online counterpart to Host Recon: RDAP WHOIS (no local `whois` binary needed), IP geolocation & ASN/ISP (via [ipwho.is](https://ipwho.is)), subdomain enumeration via certificate-transparency logs ([crt.sh](https://crt.sh)), plus optional Shodan host lookup and [AbuseIPDB](https://www.abuseipdb.com) reputation scoring if you supply your own API keys. |
| **Username Recon** | Sherlock/theHarvester-style public footprint check — tests whether a username has a public profile on ~10 major platforms (GitHub, GitLab, Steam, YouTube, npm, PyPI, Docker Hub, Keybase, Hacker News, Dev.to) via ordinary HTTP requests. No login, no scraping beyond "does a profile exist here." |
| **Breach Check** | Checks a password against HaveIBeenPwned's Pwned Passwords dataset using k-anonymity — only a 5-character SHA-1 prefix is ever sent, so the real password never leaves your machine. |
| **Settings** | Local-only storage for the optional Shodan and AbuseIPDB API keys (`~/.config/jegeo/settings.json`, owner-only permissions). Nothing here is transmitted by the panel itself. |

Every module streams its output into a color-coded console with the same
"operator console" feel as the boot sequence, and every scan/lookup runs on
a background thread so the UI never locks up — with a working **ABORT**
button.

## Ethics / scope

These are legitimate, dual-use security and networking/OSINT utilities —
the kind you'd find in any pentesting distro — presented through an
immersive UI, **not** exploit tooling. Only point the Network Scanner,
Host Recon, Wi-Fi Recon, OSINT Intel, or Username Recon modules at
systems, domains, accounts, and networks **you own or are explicitly
authorized to research.** The online modules send the target you enter
(and, for Shodan/AbuseIPDB, your API key) to third-party services
(rdap.org, ipwho.is, crt.sh, haveibeenpwned.com, api.shodan.io,
api.abuseipdb.com, and the platforms Username Recon probes) — each
module's in-app notice banner says exactly what leaves the machine.
Username Recon deliberately stops at "does a public profile exist" via
ordinary HTTP requests — it does not scrape search engines, aggregate
data-broker/people-search sites, or pull private data (friends lists,
posts, DMs). The Hash ID and Password Audit modules ship with a small (a
few hundred entries) hand-written sample of common passwords for
demonstrating *why* weak secrets are weak — it is not a real
credential-cracking wordlist. Shodan and AbuseIPDB access uses your own
account and its own terms/quota; get keys at
[shodan.io](https://www.shodan.io) and
[abuseipdb.com](https://www.abuseipdb.com) if you want those checks
enabled.

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
    http.py                # shared requests-based GET helper (timeout + UA)
    settings.py             # local JSON API-key store (~/.config/jegeo/settings.json)
  widgets/
    boot_screen.py         # animated startup sequence
    hud_overlay.py          # corner brackets + scanline sweep
    dashboard.py            # sidebar + module switcher
    module_button.py        # sidebar entry
    terminal_output.py      # color-coded console widget
  modules/
    base.py                 # shared module chrome (header, controls, console, execute/abort/export)
    network_scanner.py
    host_recon.py
    wifi_recon.py
    osint_intel.py           # online: RDAP / geolocation / crt.sh / Shodan / AbuseIPDB
    username_recon.py        # online: public profile footprint check
    breach_check.py          # online: HIBP Pwned Passwords
    sys_recon.py
    crypto_toolkit.py
    hash_id.py
    password_audit.py
    steg_tool.py
    settings_panel.py        # local Shodan / AbuseIPDB API key entry
scripts/install-fedora.sh
```

## Adding a new module

Subclass `jegeo.modules.base.BaseModule`, implement `build_controls()`
(your input widgets) and `make_task()` (returns a `task(emit, is_cancelled)`
callable that does the work off the GUI thread, calling `emit(text, level)`
to stream output — levels are `info`, `meta`, `warn`, `error`, `success`,
`cyan`), then add the class to `MODULE_CLASSES` in `jegeo/app.py`. Every
module gets EXECUTE/ABORT/EXPORT and the console for free from
`BaseModule` — EXPORT saves the console's current plain-text contents to a
file the user picks, no per-module work required.

## License

MIT. This is a fan-inspired, original implementation — no assets, code, or
branding from Ubisoft or Rainbow Six Siege are included.
