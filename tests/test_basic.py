import unittest
import os
import tempfile
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.utils.file_handler import read_txt, read_file
from src.core.tts_manager import TTSManager
from src.core.audio_player import AudioPlayer

class TestFileHandler(unittest.TestCase):
    def test_read_txt(self):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', encoding='utf-8') as tmp:
            tmp.write("Hello World")
            tmp_path = tmp.name

        try:
            content = read_txt(tmp_path)
            self.assertEqual(content, "Hello World")
            content_generic = read_file(tmp_path)
            self.assertEqual(content_generic, "Hello World")
        finally:
            os.remove(tmp_path)

class TestTTSManager(unittest.TestCase):
    @patch('src.core.tts_manager.edge_tts.list_voices', new_callable=AsyncMock)
    def test_get_voices(self, mock_list_voices):
        mock_list_voices.return_value = [{'ShortName': 'vi-VN-Test', 'Locale': 'vi-VN'}]

        manager = TTSManager()
        voices = asyncio.run(manager.get_voices())
        self.assertEqual(len(voices), 1)
        self.assertEqual(voices[0]['ShortName'], 'vi-VN-Test')

class TestAudioPlayer(unittest.TestCase):
    @patch('src.core.audio_player.pygame.mixer')
    def test_init(self, mock_mixer):
        # We need to simulate init throwing error or succeeding.
        # But AudioPlayer constructor catches error.
        player = AudioPlayer()
        mock_mixer.init.assert_called()

    @patch('src.core.audio_player.pygame.mixer.music')
    @patch('src.core.audio_player.pygame.mixer')
    def test_commands(self, mock_mixer, mock_music):
        # Mock init to succeed (or fail silently as per code)
        player = AudioPlayer()

        player.load("dummy.mp3")
        mock_music.load.assert_called_with("dummy.mp3")

        player.play()
        mock_music.play.assert_called()

        player.stop()
        mock_music.stop.assert_called()

if __name__ == '__main__':
    unittest.main()
