import os
import asyncio
import threading
import tempfile
from pathlib import Path
from quadroid.config import Config
from quadroid.audio.player import play_sound_async

# Offline TTS Engine
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Online Neural TTS Engine
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


class TTSEngine:
    """Text-to-Speech Engine supporting offline pyttsx3 and online edge-tts."""

    def __init__(self):
        self._lock = threading.Lock()
        self.offline_engine = None
        if PYTTSX3_AVAILABLE:
            try:
                self.offline_engine = pyttsx3.init()
                self.offline_engine.setProperty('rate', 185)  # Natural speech speed
                self.offline_engine.setProperty('volume', 0.95)
            except Exception:
                self.offline_engine = None

    def speak(self, text: str, async_mode: bool = True):
        """
        Speak text out loud.
        
        :param text: Text string to synthesize and speak.
        :param async_mode: If True, runs speech in background thread.
        """
        text = text.strip()
        if not text:
            return

        if async_mode:
            threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()
        else:
            self._speak_sync(text)

    def _speak_sync(self, text: str):
        with self._lock:
            # Check if online and edge-tts is preferred
            use_edge = (
                EDGE_TTS_AVAILABLE 
                and Config.TTS_ENGINE == "edge-tts" 
                and not Config.is_offline()
            )

            if use_edge:
                try:
                    self._speak_edge_tts(text)
                    return
                except Exception:
                    # Fallback to offline pyttsx3 on edge-tts error
                    pass

            # Offline pyttsx3 speech
            if self.offline_engine:
                try:
                    self.offline_engine.say(text)
                    self.offline_engine.runAndWait()
                except Exception:
                    # Re-init engine if stuck
                    try:
                        self.offline_engine = pyttsx3.init()
                        self.offline_engine.say(text)
                        self.offline_engine.runAndWait()
                    except Exception:
                        pass

    def _speak_edge_tts(self, text: str):
        """Synthesize using Microsoft Edge Neural Voice."""
        async def _generate_and_play():
            communicate = edge_tts.Communicate(text, Config.EDGE_TTS_VOICE)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_path = temp_file.name
            
            await communicate.save(temp_path)
            
            # Play mp3
            import subprocess
            subprocess.run(
                ["powershell", "-c", f'(New-Object Media.SoundPlayer "{temp_path}").PlaySync();'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            try:
                os.remove(temp_path)
            except Exception:
                pass

        asyncio.run(_generate_and_play())


# Global singleton instance
tts = TTSEngine()


def speak(text: str, async_mode: bool = True):
    """Global helper function to speak text."""
    tts.speak(text, async_mode=async_mode)
