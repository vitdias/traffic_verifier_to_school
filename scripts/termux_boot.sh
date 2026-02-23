#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/traffic_verifier_to_school}"
LOG_FILE="$PROJECT_DIR/logs/traffic_alerts.log"
mkdir -p "$PROJECT_DIR/logs"

while true; do
  "$PROJECT_DIR/scripts/start.sh" >> "$LOG_FILE" 2>&1 || true
  sleep 10
done
