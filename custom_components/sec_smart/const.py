DOMAIN = "sec_smart"
CONF_DEVICES = "devices"
CONF_DEVICE_ID = "id"
CONF_BASE_URL = "base_url"
CONF_POLL_INTERVAL = "poll_interval"
CONF_TOKEN = "token"
DEFAULT_BASE_URL = "https://api.sec-smart.app/v1"
DEFAULT_POLL_INTERVAL = 60

AREA_IDS = [1, 2, 3, 4, 5, 6]
# Mapping manual stages to percentage steps; evenly spaced.
MANUAL_PERCENTAGES = {
    1: 16,
    2: 33,
    3: 50,
    4: 67,
    5: 83,
    6: 100,
}

PRESET_BOOST = "boost"
PRESET_HUMIDITY = "humidity"
PRESET_CO2 = "co2"
PRESET_SCHEDULE = "schedule"
PRESET_SLEEP = "sleep"
PRESET_INACTIVE = "inactive"
SUPPORTED_PRESETS = [
    PRESET_BOOST,
    PRESET_HUMIDITY,
    PRESET_CO2,
    PRESET_SCHEDULE,
    PRESET_SLEEP,
]
