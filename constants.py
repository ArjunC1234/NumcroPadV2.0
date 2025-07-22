# constants.py
from pathlib import Path

# Grid dimensions
GRID_ROWS = 6
GRID_COLS = 5
CELL_SIZE = 60

# File paths
CONFIG_FILE = Path("data/layouts/numpad_layout.json")
MACRO_FILE = Path("data/macros.json")
RAWINPUTHANDLER_FILE = Path("CSDeviceListener/RawInputListener/RawInputListener/bin/Debug/net8.0-windows/RawInputListener.exe")

SETTINGS_FILE = Path("data/settings.json")

UNIQUE_APP_ID = "NUMCRO123456"  # Must be unique per app