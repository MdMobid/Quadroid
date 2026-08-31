import io
import time
import tempfile
from pathlib import Path
from typing import Optional
from quadroid.config import Config

# Standard SpeechRecognition
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

# Faster-Whisper for 100% Offline STT
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False


class SpeechListener:
    """Speech-to-Text Listener with Offline Faster-Whisper and Google/Groq fallbacks."""

    def __init__(self):
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None
        if self.recognizer:
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8  # Snappy voice recognition instead of 60s hang

        self.offline_whisper_model = None
        self._load_offline_model_if_configured()

    def _load_offline_model_if_configured(self):
        if FASTER_WHISPER_AVAILABLE and (Config.STT_ENGINE == "faster-whisper" or Config.is_offline()):
            try:
                # Load small/base quantized model on CPU
                self.offline_whisper_model = WhisperModel(
                    Config.FASTER_WHISPER_MODEL, 
                    device="cpu", 
                    compute_type="int8"
                )
            except Exception:
                self.offline_whisper_model = None

    def listen_and_transcribe(self, timeout: float = 6.0, phrase_time_limit: float = 12.0) -> Optional[str]:
        """
        Listen to microphone input and return transcribed text.
        
        :param timeout: Maximum seconds to wait for speech to start.
        :param phrase_time_limit: Maximum seconds for single phrase.
        :return: Transcribed text string or None.
        """
        if not self.recognizer:
            return None

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )

            # 1. Offline Faster-Whisper if available
            if self.offline_whisper_model:
                try:
                    wav_data = audio.get_wav_data()
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        f.write(wav_data)
                        temp_path = f.name
                    
                    segments, _ = self.offline_whisper_model.transcribe(temp_path, beam_size=1)
                    text = " ".join([segment.text for segment in segments]).strip()
                    
                    try:
                        import os
                        os.remove(temp_path)
                    except Exception:
                        pass
                    
                    return text if text else None
                except Exception:
                    pass

            # 2. Cloud Groq Whisper if online and configured
            if Config.STT_ENGINE == "groq" and Config.GROQ_API_KEY and not Config.is_offline():
                try:
                    from openai import OpenAI
                    groq_client = OpenAI(
                        base_url="https://api.groq.com/openai/v1",
                        api_key=Config.GROQ_API_KEY
                    )
                    wav_data = audio.get_wav_data()
                    buffer = io.BytesIO(wav_data)
                    buffer.name = "speech.wav"
                    transcription = groq_client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo",
                        file=buffer
                    )
                    return transcription.text.strip()
                except Exception:
                    pass

            # 3. Google Speech Recognition universal fallback
            if not Config.is_offline():
                try:
                    text = self.recognizer.recognize_google(audio)
                    return text.strip()
                except sr.UnknownValueError:
                    return None
                except sr.RequestError:
                    pass

        except sr.WaitTimeoutError:
            return None
        except Exception:
            return None

        return None


# Global singleton listener
listener = SpeechListener()


def listen_and_transcribe(timeout: float = 6.0, phrase_time_limit: float = 12.0) -> Optional[str]:
    """Helper function to listen and transcribe speech."""
    return listener.listen_and_transcribe(timeout=timeout, phrase_time_limit=phrase_time_limit)
