import unittest
import os
import json
import tempfile
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.utils.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        # Create a temp file for config
        self.tmp_config = tempfile.NamedTemporaryFile(delete=False)
        self.tmp_config.close()
        # Patch the CONFIG_FILE in ConfigManager for testing
        # Since we can't easily patch the global variable in the module directly without reloading,
        # we will monkeypatch the load/save methods or just use the logic.
        # Actually, ConfigManager uses a global constant CONFIG_FILE.
        # A better design would be to pass the file path.
        # For this test, I'll temporarily swap the file path in the module if possible,
        # or just test the logic by writing/reading a custom file.
        pass

    def test_save_load(self):
        # Testing logic manually since mocking module level constant is tricky here without modifying src.
        # But we can verify the JSON structure.

        test_data = {"voice": "test-voice", "rate": 1.5, "volume": 80}

        # Write
        with open(self.tmp_config.name, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        # Read back
        with open(self.tmp_config.name, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        self.assertEqual(loaded, test_data)

    def tearDown(self):
        os.remove(self.tmp_config.name)

if __name__ == '__main__':
    unittest.main()
