#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE" >/dev/null 2>&1 || true
  set +a
fi

if [[ -z "${STITCH_API_KEY:-}" ]]; then
  echo "STITCH_API_KEY is not set. Add it to .env or export it before launch." >&2
  exit 1
fi

export CI=1
export DOTENV_CONFIG_QUIET=true
export DOTENV_QUIET=true
export NO_COLOR=1

exec npx -y @_davideast/stitch-mcp@latest proxy
