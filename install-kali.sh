#!/usr/bin/env bash
# Infinity X — install xwifi (senza PyPI, senza errori scapy)
set -euo pipefail

echo "[*] xwifi v1.0.2 — Created by Infinity X"
echo "[*] Cartella: $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "[-] Esegui con sudo: sudo ./install-kali.sh"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y python3 python3-pip python3-scapy iptables nmap iproute2

PIP_FLAGS=(--break-system-packages)
if ! python3 -m pip install --help 2>/dev/null | grep -q break-system-packages; then
  PIP_FLAGS=()
fi

python3 -m pip install "${PIP_FLAGS[@]}" --upgrade pip wheel
python3 -m pip install "${PIP_FLAGS[@]}" "rich>=10.0.0"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEEL="${SCRIPT_DIR}/dist/xwifi-1.0.2-py3-none-any.whl"

if [[ ! -f "$WHEEL" ]]; then
  echo "[*] Wheel non trovato — build locale…"
  python3 -m pip install "${PIP_FLAGS[@]}" build
  (cd "$SCRIPT_DIR" && python3 -m build -w)
fi

if [[ -f "$WHEEL" ]]; then
  python3 -m pip install "${PIP_FLAGS[@]}" --force-reinstall --no-deps "$WHEEL"
else
  echo "[*] Install da sorgente…"
  python3 -m pip install "${PIP_FLAGS[@]}" --force-reinstall "$SCRIPT_DIR"
fi

echo ""
echo "[+] Installazione OK."
if command -v xwifi >/dev/null 2>&1; then
  echo "[+] Avvia: sudo xwifi"
else
  echo "[+] Avvia: sudo python3 -m xwifi"
fi
