import re
import time
import threading
from typing import Callable, Optional
from quadroid.config import Config
from quadroid.audio.player import play_sound_async
from quadroid.audio.speech import is_speaking

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


class WakeWordListener:
    """High-sensitivity background listener that detects 'Hey [Nickname]' or 'Quadroid' with phonetic tolerance."""

    def __init__(self, on_wake_detected: Optional[Callable[[], None]] = None):
        self.on_wake_detected = on_wake_detected
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        
        # Build comprehensive phonetic variations for wake triggers
        word = Config.WAKE_WORD.lower().strip()
        
        # Common phonetic transcriptions for "max" or custom nicknames
        phonetic_aliases = [
            word,
            f"hey {word}",
            f"ok {word}",
            f"hello {word}",
            f"hi {word}",
            f"he {word}",
            f"yo {word}",
            "quadroid",
            "hey quadroid",
            "ok quadroid",
            "hello quadroid",
            "hi quadroid"
        ]
        
        if word == "max":
            phonetic_aliases.extend([
                "macs", "marks", "macks", "match", "matt", "mex", "max.",
                "hey macs", "hey marks", "hey macks", "hey mex"
            ])
            
        self.wake_words = list(set(phonetic_aliases))
        # Regex pattern for boundary matching
        pattern_str = r'\b(' + '|'.join(re.escape(w) for w in self.wake_words) + r')\b'
        self.wake_regex = re.compile(pattern_str, re.IGNORECASE)

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
        
        # Optimized microphone sensitivity
        recognizer.energy_threshold = 220
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_damping = 0.15
        recognizer.dynamic_energy_ratio = 1.3
        recognizer.pause_threshold = 0.5
        recognizer.non_speaking_duration = 0.3

        # Calibrate once at startup
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
        except Exception:
            pass

        while self.is_running:
            # If assistant is currently speaking through speakers, pause listening
            if is_speaking():
                time.sleep(0.2)
                continue

            try:
                with sr.Microphone() as source:
                    audio = recognizer.listen(source, timeout=2.0, phrase_time_limit=3.0)

                if is_speaking():
                    continue

                try:
                    # Recognize speech using Google STT
                    text = recognizer.recognize_google(audio).lower().strip()
                    
                    # Check wake word match with phonetic tolerance
                    if self.wake_regex.search(text) or any(w in text for w in self.wake_words):
                        # Play pleasant wake sound
                        play_sound_async("wake-up.mp3")
                        
                        # Trigger callback
                        if self.on_wake_detected:
                            self.on_wake_detected()
                        
                        # Safety pause after wake trigger
                        time.sleep(1.2)
                except (sr.UnknownValueError, sr.RequestError):
                    continue

            except sr.WaitTimeoutError:
                continue
            except Exception:
                time.sleep(0.5)
                continue
