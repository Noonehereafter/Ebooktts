import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
    @staticmethod
    def load_config():
        default_config = {
            "voice": "vi-VN-HoaiMyNeural",
            "rate": 1.0,
            "volume": 100,
            "pitch": 0,
            "recent_files": []
        }
        if not os.path.exists(CONFIG_FILE):
            return default_config

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with default to ensure all keys exist
                for key, val in default_config.items():
                    if key not in config:
                        config[key] = val
                return config
        except Exception:
            return default_config

    @staticmethod
    def save_config(config):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    @staticmethod
    def add_recent_file(config, filepath):
        recents = config.get("recent_files", [])
        if filepath in recents:
            recents.remove(filepath)
        recents.insert(0, filepath)
        config["recent_files"] = recents[:5] # Keep last 5
        return config
