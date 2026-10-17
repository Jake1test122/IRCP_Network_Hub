#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -z "${DISCORD_TOKEN:-}" || -z "${ICRP_SERVER_ID:-}" ]]; then
  echo 'Missing DISCORD_TOKEN or ICRP_SERVER_ID. Set them as Codespaces secrets.'
  exit 1
fi
python -m pip install -r requirements_icrp_community.txt
exec python icrp_community_bot.py
