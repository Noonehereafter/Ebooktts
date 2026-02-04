import edge_tts
import asyncio

class TTSManager:
    async def get_voices(self):
        """Fetches available voices from Edge TTS."""
        try:
            voices = await edge_tts.list_voices()
            return voices
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []

    async def save_audio(self, text, voice, rate, volume, output_file):
        """
        Generates audio from text.

        Args:
            text (str): Text to speak.
            voice (str): Voice short name (e.g., 'vi-VN-HoaiMyNeural').
            rate (float): Speed multiplier (1.0 is normal).
            volume (int): Volume percentage (100 is normal).
            output_file (str): Path to save audio.
        """
        try:
            # Format rate
            # rate=1.0 -> +0%
            # rate=1.5 -> +50%
            # rate=0.5 -> -50%
            rate_percentage = int((rate - 1.0) * 100)
            rate_str = f"{rate_percentage:+d}%"

            # Format volume
            # volume=100 -> +0%
            # volume=50 -> -50%
            volume_diff = int(volume - 100)
            volume_str = f"{volume_diff:+d}%"

            communicate = edge_tts.Communicate(text, voice, rate=rate_str, volume=volume_str)
            await communicate.save(output_file)
        except Exception as e:
            raise Exception(f"TTS Generation Error: {e}")
