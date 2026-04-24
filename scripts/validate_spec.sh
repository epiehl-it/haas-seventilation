#!/usr/bin/env bash
# Runs openapi-python-client against `openapi.json` purely as a spec
# validator. The generated client is written to a scratch directory and
# discarded — we do not ship a generated client (HA integrations are
# expected to use aiohttp directly).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRATCH="$ROOT/.generated-client"

rm -rf "$SCRATCH"
mkdir -p "$SCRATCH"

cd "$SCRATCH"
uv run --project "$ROOT" openapi-python-client generate --path "$ROOT/openapi.json" "$@"
