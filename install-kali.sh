#!/usr/bin/env bash
# Infinity X — install xwifi su Kali (no upgrade pip/wheel Debian)
set -euo pipefail

echo "[*] xwifi v1.0.4 — Created by Infinity X"
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

# Non fare upgrade di pip/wheel: su Kali sono pacchetti .deb e pip fallisce con uninstall-no-record-file
ensure_rich() {
  if python3 -c "import rich" 2>/dev/null; then
    return 0
  fi
  if apt-get install -y python3-rich 2>/dev/null; then
    python3 -c "import rich" 2>/dev/null && return 0
  fi
  echo "[*] Install rich via pip (ignore-installed)…"
  python3 -m pip install "${PIP_FLAGS[@]}" --ignore-installed "rich>=10.0.0"
}

ensure_rich

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Install pacchetto xwifi…"
python3 -m pip install "${PIP_FLAGS[@]}" --force-reinstall "$SCRIPT_DIR"

# Su Kali sudo spesso non ha /usr/local/bin nel PATH → "xwifi: command not found"
install -d /usr/bin
cat > /usr/bin/xwifi << 'EOF'
#!/usr/bin/env python3
from xwifi.cli import main

if __name__ == "__main__":
    main()
EOF
chmod 755 /usr/bin/xwifi

echo ""
echo "[+] Installazione OK."
echo "[+] Avvia: sudo xwifi"
