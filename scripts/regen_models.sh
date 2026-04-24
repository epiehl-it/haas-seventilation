#!/usr/bin/env bash
# Regenerates `custom_components/sec_smart/models.py` from the patched
# `openapi.json` using datamodel-code-generator. TypedDicts are used so
# the custom component does not gain a runtime dependency (HACS-friendly).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SPEC="$ROOT/openapi.json"
OUT="$ROOT/custom_components/sec_smart/models.py"

uv run datamodel-codegen \
    --input "$SPEC" \
    --input-file-type openapi \
    --output "$OUT" \
    --output-model-type typing.TypedDict \
    --target-python-version 3.13 \
    --use-schema-description \
    --use-field-description \
    --disable-timestamp

echo "Wrote $OUT"
