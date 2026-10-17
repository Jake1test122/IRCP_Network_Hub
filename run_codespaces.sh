#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -z "${DISCORD_TOKEN:-}" || -z "${SERVER_ID:-}" ]]; then
  echo "Missing DISCORD_TOKEN or SERVER_ID."
  echo "Add them under Codespaces repository secrets, then rebuild the Codespace."
  exit 1
fi
python -m pip install --user -r requirements.txt
exec python main.py
