import edge_tts
import asyncio
import os
import tempfile
from pydub import AudioSegment

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
        """Generates audio from text."""
        try:
            rate_percentage = int((rate - 1.0) * 100)
            rate_str = f"{rate_percentage:+d}%"

            volume_diff = int(volume - 100)
            volume_str = f"{volume_diff:+d}%"

            communicate = edge_tts.Communicate(text, voice, rate=rate_str, volume=volume_str)
            await communicate.save(output_file)
        except Exception as e:
            raise Exception(f"TTS Generation Error: {e}")

    async def generate_audio_with_silence(self, segments, voice, rate, volume, output_file, progress_callback=None):
        """
        Generates audio for subtitle segments and positions them on a timeline.

        Args:
            segments (list): List of dicts {'start': ms, 'end': ms, 'text': str}
            voice, rate, volume: TTS params
            output_file: Path to save result
            progress_callback: Function(current, total)
        """
        if not segments:
            raise Exception("No subtitle segments found.")

        # Determine total duration
        total_duration = segments[-1]['end'] + 1000 # Add buffer at end
        base_audio = AudioSegment.silent(duration=total_duration)

        temp_dir = tempfile.gettempdir()

        try:
            total_segments = len(segments)
            for i, seg in enumerate(segments):
                text = seg['text']
                if not text.strip():
                    continue

                # Generate clip
                temp_clip_path = os.path.join(temp_dir, f"temp_tts_clip_{i}.mp3")
                await self.save_audio(text, voice, rate, volume, temp_clip_path)

                # Load clip
                clip = AudioSegment.from_mp3(temp_clip_path)

                # Overlay
                # Note: If clip is longer than the gap to next segment, it might overlap.
                # User requirement: "có khoảng trống ko có audio nhưng vẫn phải có audio đủ dài"
                # This implies: If TTS is shorter than (end-start), leave silence.
                # If TTS is longer, it will just extend (possibly overlapping next segment start).
                # To be robust, we just overlay at 'start'. If it overlaps next, Pydub handles it by mixing.
                # But audiobooks usually shouldn't overlap.
                # For now, we assume simple overlay.
                base_audio = base_audio.overlay(clip, position=seg['start'])

                # Cleanup clip
                if os.path.exists(temp_clip_path):
                    os.remove(temp_clip_path)

                if progress_callback:
                    progress_callback(i+1, total_segments)

            # Export final
            base_audio.export(output_file, format="mp3")

        except Exception as e:
            raise Exception(f"Subtitle Sync Error: {e}")
