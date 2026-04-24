#!/usr/bin/env bash
# Fetches the current upstream SEC Smart OpenAPI spec and writes it to
# /tmp/sec_smart_upstream_openapi.json for comparison with the patched
# `openapi.json` in this repo.
#
# The upstream spec is served inlined inside swagger-ui-init.js, so we
# extract the `swaggerDoc` object with a small Python helper.

set -euo pipefail

INIT_JS="$(mktemp -t sec_smart_swagger_init.XXXXXX.js)"
OUT="${1:-/tmp/sec_smart_upstream_openapi.json}"

trap 'rm -f "$INIT_JS"' EXIT

curl -sfL https://api.sec-smart.app/v1/api-docs/swagger-ui-init.js -o "$INIT_JS"

python3 - "$INIT_JS" "$OUT" <<'PY'
import json, re, sys
src, dst = sys.argv[1], sys.argv[2]
with open(src) as f:
    content = f.read()
m = re.search(r'"swaggerDoc"\s*:\s*', content)
if not m:
    sys.exit("swaggerDoc not found in swagger-ui-init.js")
start = m.end()
depth, i = 0, start
in_str = esc = False
while i < len(content):
    c = content[i]
    if esc:
        esc = False
    elif c == '\\':
        esc = True
    elif c == '"':
        in_str = not in_str
    elif not in_str:
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    i += 1
spec = json.loads(content[start:end])
with open(dst, 'w') as f:
    json.dump(spec, f, indent=2, ensure_ascii=False)
    f.write('\n')
print(f"Wrote {dst}")
PY
