import os
import asyncio
import threading
import tempfile
import logging
from pathlib import Path
from quadroid.config import Config
from quadroid.audio.player import play_sound_async

# Suppress pygame startup banner
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

logger = logging.getLogger(__name__)

# Global speech activity flag
_is_speaking_lock = threading.Lock()
_is_speaking = False

def is_speaking() -> bool:
    """Return True if TTS is actively speaking audio through speakers."""
    return _is_speaking

# Pygame Audio Player
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Offline TTS Engine
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Online Neural TTS Engine (Edge-TTS)
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


class TTSEngine:
    """Ultra-realistic Neural Text-to-Speech Engine with human-like prosody and pygame high-fidelity playback."""

    def __init__(self):
        self._lock = threading.Lock()
        self.offline_engine = None
        
        # Init pygame mixer for high-fidelity audio
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception:
                pass

        if PYTTSX3_AVAILABLE:
            try:
                self.offline_engine = pyttsx3.init()
                self.offline_engine.setProperty('rate', 175)  # Natural speed
                self.offline_engine.setProperty('volume', 0.95)
            except Exception:
                self.offline_engine = None

    def speak(self, text: str, async_mode: bool = True):
        """
        Speak text out loud using ultra-realistic Microsoft Neural voice.
        
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
        global _is_speaking
        with self._lock:
            try:
                _is_speaking = True
                
                # Check if online and edge-tts is preferred (Hyper-realistic Human Neural Voice)
                use_edge = (
                    EDGE_TTS_AVAILABLE 
                    and Config.TTS_ENGINE == "edge-tts" 
                    and not Config.is_offline()
                )

                if use_edge:
                    try:
                        self._speak_edge_tts(text)
                        return
                    except Exception as e:
                        logger.warning(f"Edge-TTS failed ({e}), falling back to offline voice.")

                # Offline pyttsx3 fallback
                if self.offline_engine:
                    try:
                        self.offline_engine.say(text)
                        self.offline_engine.runAndWait()
                    except Exception:
                        try:
                            self.offline_engine = pyttsx3.init()
                            self.offline_engine.say(text)
                            self.offline_engine.runAndWait()
                        except Exception:
                            pass
            finally:
                _is_speaking = False

    def _speak_edge_tts(self, text: str):
        """Synthesize using Microsoft Edge Neural Voice with zero-latency Pygame playback."""
        async def _generate():
            voice = Config.EDGE_TTS_VOICE or "en-US-ChristopherNeural"
            communicate = edge_tts.Communicate(text, voice)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_path = temp_file.name
            await communicate.save(temp_path)
            return temp_path

        temp_path = asyncio.run(_generate())

        try:
            if PYGAME_AVAILABLE:
                import time
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.04)
                pygame.mixer.music.unload()
            else:
                # Windows fallback
                import subprocess
                subprocess.run(
                    ["powershell", "-c", f'(New-Object Media.SoundPlayer "{temp_path}").PlaySync();'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass


# Global singleton instance
tts = TTSEngine()


def speak(text: str, async_mode: bool = True):
    """Global helper function to speak text."""
    tts.speak(text, async_mode=async_mode)
