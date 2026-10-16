#!/usr/bin/env bash
# Pubblica su PyPI così funziona: pip install xwifi
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install --upgrade build twine
python3 -m build
twine upload dist/xwifi-1.0.2*
