"""Patch the SEC Smart OpenAPI spec so it parses with openapi-python-client.

Upstream (`api.sec-smart.app/v1/api-docs/`) ships a spec with:

- ~30 ``$ref`` values that point into sub-properties
  (``#/components/schemas/Device/properties/name`` etc.). JSON Schema
  allows this in principle but openapi-python-client refuses them.
- ``"oneOf": null`` sprinkled through 400-response schemas.
- Missing ``"type": "object"`` on nearly every composite schema.
- A few invalid ``format`` values on Telemetry strings.

This script rewrites ``openapi.json`` in place. It is idempotent: running
it on an already-patched spec produces no further changes.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

SPEC = Path(__file__).resolve().parents[1] / "openapi.json"


# Deep-$ref target -> new flat schema name. The left side omits the
# leading "#/components/schemas/".
PROMOTIONS: dict[str, str] = {
    # Data sub-properties referenced by request bodies.
    "Device/properties/name": "DeviceName",
    "Area/properties/mode": "AreaMode",
    "Area/properties/label": "AreaLabel",
    "Area/properties/timers": "AreaTimers",
    "Filter/properties/maxRunTime": "FilterMaxRunTime",
    "Settings/properties/sleepTime": "SettingsSleepTime",
    "Settings/properties/deviceTime": "SettingsDeviceTime",
    "Settings/properties/summermode": "SettingsSummerMode",
    "Setup/properties/systems": "SetupSystems",
    "Setup/properties/areas": "SetupAreas",
    "Setup/properties/inputDi": "SetupInputDi",
    "Setup/properties/inputAi": "SetupInputAi",
    "Setup/properties/outputDo": "SetupOutputDo",
    # Error leaves referenced by 400-responses.
    "Error/properties/DeviceErrors": "DeviceErrors",
    "Error/properties/AreasErrors/properties/ModeErrors": "AreaModeErrors",
    "Error/properties/AreasErrors/properties/LabelErrors": "AreaLabelErrors",
    "Error/properties/AreasErrors/properties/TimerErrors": "AreaTimerErrors",
    "Error/properties/SettingsErrors/properties/FilterErrors": "SettingsFilterErrors",
    "Error/properties/SettingsErrors/properties/ThresholdsErrors": "SettingsThresholdsErrors",
    "Error/properties/SettingsErrors/properties/SleepTimeErrors": "SettingsSleepTimeErrors",
    "Error/properties/SettingsErrors/properties/DeviceTimeErrors": "SettingsDeviceTimeErrors",
    "Error/properties/SettingsErrors/properties/SummerModeErrors": "SettingsSummerModeErrors",
    "Error/properties/SetupErrors/properties/SystemsErrors": "SetupSystemsErrors",
    "Error/properties/SetupErrors/properties/AreasBoostsErrors": "SetupAreasBoostsErrors",
    "Error/properties/SetupErrors/properties/DigitalInputErrors": "SetupDigitalInputErrors",
    "Error/properties/SetupErrors/properties/AnalogInputErrors": "SetupAnalogInputErrors",
    "Error/properties/SetupErrors/properties/DigitalOutputErrors": "SetupDigitalOutputErrors",
    "Error/properties/SetupErrors/properties/FactoryResetErrors": "SetupFactoryResetErrors",
}


def resolve_deep_path(schemas: dict, path: str) -> dict:
    node = schemas
    for part in path.split("/"):
        node = node[part]
    return node


def resolve_deep_parent(schemas: dict, path: str) -> tuple[dict, str]:
    parts = path.split("/")
    node = schemas
    for part in parts[:-1]:
        node = node[part]
    return node, parts[-1]


def promote_deep_refs(spec: dict) -> None:
    """Promote each deep-$ref target to a top-level schema and replace
    the original inline definition with a $ref so we don't end up with
    two definitions of the same object (openapi-python-client rejects
    duplicates on complex-object schemas)."""
    schemas = spec["components"]["schemas"]

    for src, new_name in PROMOTIONS.items():
        if new_name in schemas:
            continue  # already promoted (idempotent)
        target = deepcopy(resolve_deep_path(schemas, src))
        schemas[new_name] = target
        parent, last_key = resolve_deep_parent(schemas, src)
        parent[last_key] = {"$ref": f"#/components/schemas/{new_name}"}


def rewrite_refs(node) -> None:
    """Walk the tree; rewrite deep $refs to their promoted flat names."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            suffix = ref[len("#/components/schemas/"):]
            if suffix in PROMOTIONS:
                node["$ref"] = f"#/components/schemas/{PROMOTIONS[suffix]}"
        for v in node.values():
            rewrite_refs(v)
    elif isinstance(node, list):
        for v in node:
            rewrite_refs(v)


def strip_oneof_null(node) -> None:
    """Remove ``"oneOf": null`` artifacts so validators accept the spec."""
    if isinstance(node, dict):
        if node.get("oneOf", "__missing__") is None:
            node.pop("oneOf")
        for v in node.values():
            strip_oneof_null(v)
    elif isinstance(node, list):
        for v in node:
            strip_oneof_null(v)


def add_missing_object_types(node) -> None:
    """Any schema with ``properties`` but no ``type`` is an object."""
    if isinstance(node, dict):
        if "properties" in node and "type" not in node and "$ref" not in node:
            # Preserve key order so "type" appears before "properties".
            ordered = {"type": "object"}
            ordered.update(node)
            node.clear()
            node.update(ordered)
        for v in node.values():
            add_missing_object_types(v)
    elif isinstance(node, list):
        for v in node:
            add_missing_object_types(v)


def fix_telemetry_formats(spec: dict) -> None:
    """Drop invalid ``format`` values on string telemetry fields.

    ``"CC.C"`` and ``"yy.ddd.hh:mm"`` are vendor-specific placeholders that
    no validator understands. Keep ``type: string`` and the example;
    describe the shape in the description instead.
    """
    telemetry = spec["components"]["schemas"].get("Telemetry", {})
    props = telemetry.get("properties", {})
    for field in ("Ti", "Ta", "uptime"):
        if field in props and "format" in props[field]:
            fmt = props[field].pop("format")
            desc = props[field].get("description", "")
            if fmt and fmt not in desc:
                props[field]["description"] = f"{desc} (format: {fmt})".strip()

    last_message = spec["components"]["schemas"].get(
        "Notifications", {}
    ).get("properties", {}).get("lastMessage", {}).get("properties", {})
    for field in ("date", "time"):
        if field in last_message and "format" in last_message[field]:
            fmt = last_message[field]["format"]
            if fmt and fmt.startswith("ISO 8601"):
                last_message[field]["format"] = "date" if field == "date" else "time"


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))

    promote_deep_refs(spec)
    rewrite_refs(spec)
    strip_oneof_null(spec)
    add_missing_object_types(spec)
    fix_telemetry_formats(spec)

    SPEC.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Patched {SPEC}")


if __name__ == "__main__":
    main()
