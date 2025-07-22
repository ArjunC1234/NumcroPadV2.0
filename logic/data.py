from constants import SETTINGS_FILE
import json

def load_settings(parent):
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
def save_settings(parent):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(parent.settings, f, indent=2)
    except Exception as e:
        print(f"Failed to save settings: {e}")


