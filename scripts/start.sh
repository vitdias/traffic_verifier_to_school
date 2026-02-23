#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/traffic_verifier_to_school}"
cd "$PROJECT_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONPATH="$PROJECT_DIR/src"
python -m traffic_alerts.main
