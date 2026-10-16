"""Check runtime dependencies before starting the CLI."""

from __future__ import annotations

import sys


def ensure_dependencies() -> None:
    missing: list[str] = []
    try:
        import rich  # noqa: F401
    except ImportError:
        missing.append("rich  →  pip3 install rich --break-system-packages")

    try:
        import scapy  # noqa: F401
    except ImportError:
        missing.append(
            "scapy  →  sudo apt install -y python3-scapy  (consigliato su Kali)"
        )

    if missing:
        print("\n[-] Dipendenze mancanti per xwifi:\n")
        for line in missing:
            print(f"    • {line}")
        print("\n    Oppure: sudo ./install-kali.sh\n")
        sys.exit(1)
