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

    async def save_audio(self, text, voice, rate, volume, output_file, pitch=0):
        """Generates audio from text."""
        try:
            rate_percentage = int((rate - 1.0) * 100)
            rate_str = f"{rate_percentage:+d}%"

            volume_diff = int(volume - 100)
            volume_str = f"{volume_diff:+d}%"

            pitch_str = f"{int(pitch):+d}Hz"

            communicate = edge_tts.Communicate(text, voice, rate=rate_str, volume=volume_str, pitch=pitch_str)
            await communicate.save(output_file)
        except Exception as e:
            raise Exception(f"TTS Generation Error: {e}")

    async def generate_audio_with_silence(self, segments, voice, rate, volume, output_file, progress_callback=None, pitch=0):
        """
        Generates audio for subtitle segments using Linear Append strategy.
        This ensures memory efficiency and handles gaps/overlaps gracefully.

        Args:
            segments (list): List of dicts {'start': ms, 'end': ms, 'text': str}
            voice, rate, volume, pitch: TTS params
            output_file: Path to save result
            progress_callback: Function(current, total)
        """
        if not segments:
            raise Exception("No subtitle segments found.")

        final_audio = AudioSegment.empty()
        cursor_ms = 0

        temp_dir = tempfile.gettempdir()

        try:
            total_segments = len(segments)
            for i, seg in enumerate(segments):
                text = seg['text']
                if not text.strip():
                    continue

                target_start = seg['start']
                gap = target_start - cursor_ms

                # 1. Handle Silence (Gap)
                if gap > 0:
                    silence = AudioSegment.silent(duration=gap)
                    final_audio += silence
                    cursor_ms += gap
                elif gap < 0:
                    # Overlap detected: Previous audio was too long.
                    # We accept the drift (Audio continues immediately).
                    print(f"Warning: Segment {i} starting late by {-gap}ms")
                    # No silence added, cursor remains at end of previous clip

                # 2. Generate Audio
                temp_clip_path = os.path.join(temp_dir, f"temp_tts_clip_{i}.mp3")
                await self.save_audio(text, voice, rate, volume, temp_clip_path, pitch=pitch)

                # 3. Append Audio
                clip = AudioSegment.from_mp3(temp_clip_path)
                final_audio += clip
                cursor_ms += len(clip)

                # Cleanup
                if os.path.exists(temp_clip_path):
                    os.remove(temp_clip_path)

                if progress_callback:
                    progress_callback(i+1, total_segments)

            # Export final
            final_audio.export(output_file, format="mp3")

        except Exception as e:
            raise Exception(f"Subtitle Sync Error: {e}")
