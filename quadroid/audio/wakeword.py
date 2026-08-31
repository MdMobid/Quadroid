import time
import threading
from typing import Callable, Optional
from quadroid.config import Config
from quadroid.audio.player import play_sound_async
from quadroid.audio.listener import listen_and_transcribe

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


class WakeWordListener:
    """Continuous background listener that detects 'Hey Quadroid' or 'Quadroid'."""

    def __init__(self, on_wake_detected: Optional[Callable[[], None]] = None):
        self.on_wake_detected = on_wake_detected
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        
        # Build dynamic wake word triggers for custom nickname
        word = Config.WAKE_WORD.lower().strip()
        self.wake_words = list(set([
            word,
            f"hey {word}",
            f"ok {word}",
            f"hello {word}",
            f"hi {word}",
            "quadroid",
            "hey quadroid"
        ]))

    def start(self):
        """Start background wake-word listening."""
        if self.is_running or not SR_AVAILABLE:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop background listening."""
        self.is_running = False

    def _listen_loop(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 350
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.6

        while self.is_running:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    audio = recognizer.listen(source, timeout=3.0, phrase_time_limit=3.5)

                try:
                    # Quick phrase check
                    text = recognizer.recognize_google(audio).lower()
                    if any(w in text for w in self.wake_words):
                        # Play wake sound
                        play_sound_async("wake-up.mp3")
                        
                        # Trigger callback
                        if self.on_wake_detected:
                            self.on_wake_detected()
                        
                        # Brief pause after wake trigger
                        time.sleep(1.0)
                except (sr.UnknownValueError, sr.RequestError):
                    continue

            except sr.WaitTimeoutError:
                continue
            except Exception:
                time.sleep(1.0)
                continue
