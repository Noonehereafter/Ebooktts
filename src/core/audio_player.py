import pygame
import os

class AudioPlayer:
    def __init__(self):
        try:
            pygame.mixer.init()
        except pygame.error as e:
            print(f"Warning: Could not initialize pygame mixer: {e}")
        self.is_paused = False

    def load(self, filepath):
        """Loads an audio file."""
        try:
            pygame.mixer.music.load(filepath)
        except pygame.error as e:
            raise Exception(f"Could not load audio: {e}")

    def play(self):
        """Plays the loaded audio."""
        try:
            pygame.mixer.music.play()
            self.is_paused = False
        except Exception as e:
            print(f"Error playing audio: {e}")

    def pause(self):
        """Pauses playback."""
        try:
            pygame.mixer.music.pause()
            self.is_paused = True
        except Exception as e:
             print(f"Error pausing audio: {e}")

    def unpause(self):
        """Resumes playback."""
        try:
            pygame.mixer.music.unpause()
            self.is_paused = False
        except Exception as e:
             print(f"Error unpausing audio: {e}")

    def stop(self):
        """Stops playback."""
        try:
            pygame.mixer.music.stop()
            self.is_paused = False
        except Exception as e:
             print(f"Error stopping audio: {e}")

    def set_volume(self, volume):
        """Sets playback volume (0.0 to 1.0)."""
        try:
            # Ensure volume is clamped
            volume = max(0.0, min(1.0, volume))
            pygame.mixer.music.set_volume(volume)
        except Exception as e:
             print(f"Error setting volume: {e}")

    def get_busy(self):
        """Returns True if music is playing."""
        return pygame.mixer.music.get_busy()
