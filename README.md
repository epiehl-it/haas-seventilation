# SEC Smart Home Assistant (YAML) Integration

Einfacher Custom-Component, der die Areas (Lüftungszonen) einer SEC Smart Steuerung als `fan`-Entitäten in Home Assistant verfügbar macht. Steuerung erfolgt über den Modus (`PUT /devices/{id}/areas/mode`), Status per Polling (`GET /devices/{id}/areas`).

## Installation
- **HACS (empfohlen):** In HACS unter "Custom repositories" das Repo `https://github.com/epiehl/sev_smart_api` als Typ "Integration" hinzufügen, die Integration installieren und Home Assistant neu starten.
- **Manuell:** Kopiere den Ordner `custom_components/sec_smart` in dein Home-Assistant-Konfigurationsverzeichnis (z. B. `/config/custom_components/sec_smart`) und starte Home Assistant neu.

## Konfiguration (YAML)
Beispiel für `configuration.yaml`:
```yaml
sec_smart:
  base_url: https://api.sec-smart.app/v1
  token: !secret sec_smart_token
  poll_interval: 60  # Sek.
  devices:
    - id: "6CBA80"
      # optional: poll_interval: 30
```
Hinweise:
- `poll_interval` auf Root-Ebene ist Default für alle Geräte; pro Gerät überschreibbar.
- Areas mit Modus `INACTIVE` werden unterdrückt (z. B. area6 in deinem Beispiel).

## Unterstützte Features
- `fan`-Entitäten je aktiver Area (`area1`–`area6`).
- Prozentsteuerung → mapped auf `Manual 1..6` (Stufen 1–6 ≈ 16/33/50/67/83/100%).
- Presets (FanEntityFeature.PRESET_MODE):
  - `boost` → "Boost ventilation"
  - `humidity` → "Humidity regulation"
  - `co2` → "CO2 regulation"
  - `schedule` → "Timed program"
  - `sleep` → "Snooze"
- `turn_off` → "Fans off".
- Zusatzattribute: Timer-Objekt der Area.

## Bekannte Einschränkungen
- Kein Config-Flow; ausschließlich YAML.
- Keine Push-Updates; Polling (Default 60s).
- Keine automatische Lokalisierung der Preset-Namen in der UI; Labels aus der API werden als Entity-Namen genutzt.

## Kurze Architektur
- `SecSmartApi` (aiohttp) ruft `/devices/{id}/areas` und `/devices/{id}/areas/mode` mit Bearer-Token auf.
- `SecSmartCoordinator` (DataUpdateCoordinator) pollt Area-Status.
- `fan.py` legt je Area eine Entity an, wenn der Modus nicht `INACTIVE` ist; setzt Modus via API und triggert Refresh.

## Releases
- Version in `custom_components/sec_smart/manifest.json` muss mit dem Release-Tag übereinstimmen (z. B. `v0.1.0`).

## ToDo / Ideen
- Config-Flow (UI) hinzufügen.
- Telemetrie (CO₂, Feuchte, Temperaturen) als Sensoren anlegen.
- Fehler/Notifications als Binary-Sensor.
- Optionale Überschreibung der Area-Namen in YAML.
