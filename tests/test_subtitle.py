import unittest
import os
import sys
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.utils.file_handler import read_subtitle

class TestSubtitleHandler(unittest.TestCase):
    def test_read_srt(self):
        filepath = "tests/test_subtitle.srt"
        segments = read_subtitle(filepath)

        self.assertEqual(len(segments), 2)

        # Check first segment
        # 00:00:01,000 = 1000ms
        self.assertEqual(segments[0]['start'], 1000)
        self.assertEqual(segments[0]['end'], 3000)
        self.assertEqual(segments[0]['text'], "Hello World")

        # Check second segment
        self.assertEqual(segments[1]['start'], 5000)
        self.assertEqual(segments[1]['end'], 7000)
        self.assertEqual(segments[1]['text'], "Test Subtitle")

if __name__ == '__main__':
    unittest.main()
