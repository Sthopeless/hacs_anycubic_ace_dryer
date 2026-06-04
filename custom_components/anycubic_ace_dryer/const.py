from __future__ import annotations

DOMAIN = "anycubic_ace_dryer"

CONF_HOST = "host"
CONF_NUM_UNITS = "num_units"
CONF_UNIT_MODELS = "unit_models"

MOONRAKER_PORT = 7125
SCAN_INTERVAL = 10  # seconds

# (display_name, temp_min_°C, temp_max_°C)
# Limits are per Anycubic hardware specs; ACE 2 Pro runs hotter.
ACE_MODELS: dict[str, tuple[str, int, int]] = {
    "ace":       ("ACE",       30, 50),
    "ace_pro":   ("ACE Pro",   30, 65),
    "ace_2_pro": ("ACE 2 Pro", 30, 70),
}

MATERIAL_PRESETS: dict[str, int | None] = {
    "PLA":    45,
    "PETG":   55,
    "ABS":    65,
    "Custom": None,
}

DRYER_STATUS_STOP    = "stop"
DRYER_STATUS_DRYING  = "drying"
DRYER_STATUS_ERROR   = "heater_err"

STATUS_LABELS: dict[str, str] = {
    DRYER_STATUS_STOP:   "Stopped",
    DRYER_STATUS_DRYING: "Drying",
    DRYER_STATUS_ERROR:  "Heater Error",
}
