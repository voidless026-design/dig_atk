#!/usr/bin/env bash
# Sets up JEGEO PAYLOAD on Fedora Workstation.
#
# Installs the system packages the optional recon modules shell out to
# (NetworkManager's nmcli, whois, traceroute) plus a Python virtualenv with
# the app's own dependencies, then installs the `jegeo` command into it.
set -euo pipefail

echo "== JEGEO PAYLOAD :: Fedora setup =="

if ! command -v dnf >/dev/null 2>&1; then
    echo "This script targets Fedora (dnf not found). Install manually instead:" >&2
    echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
    exit 1
fi

echo "-- installing system packages (whois, traceroute, NetworkManager, python3-venv) --"
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-virtualenv \
    whois \
    traceroute \
    NetworkManager

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "-- creating virtual environment (.venv) --"
python3 -m venv .venv
source .venv/bin/activate

echo "-- installing Python dependencies --"
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

echo
echo "Setup complete. Launch with:"
echo "  source .venv/bin/activate"
echo "  jegeo"
echo
echo "(or, without activating: .venv/bin/jegeo)"
