import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
    @staticmethod
    def load_config():
        default_config = {
            "voice": "vi-VN-HoaiMyNeural",
            "rate": 1.0,
            "volume": 100
        }
        if not os.path.exists(CONFIG_FILE):
            return default_config

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default_config

    @staticmethod
    def save_config(config):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
