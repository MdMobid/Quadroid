import os
import threading
from pathlib import Path
from quadroid.config import Config

# Attempt winsound on Windows for zero-dependency sound playback
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


def play_sound_async(sound_filename: str):
    """
    Play a sound effect asynchronously from the 'Sound Effects' directory.
    
    :param sound_filename: Name of the sound file (e.g. 'wake-up.mp3', 'response.wav', 'interface.mp3').
    """
    sound_path = Config.SOUNDS_DIR / sound_filename
    if not sound_path.exists():
        return

    def _play():
        try:
            if sound_filename.endswith(".wav") and WINSOUND_AVAILABLE:
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Use powershell Media.SoundPlayer or simple windows media command
                import subprocess
                subprocess.Popen(
                    ["powershell", "-c", f'(New-Object Media.SoundPlayer "{str(sound_path)}").PlaySync();'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()
