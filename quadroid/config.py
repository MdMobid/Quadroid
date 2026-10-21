import os
import socket
import warnings
from pathlib import Path

# Suppress noisy HuggingFace / tokenizers notices
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
warnings.filterwarnings("ignore", module="huggingface_hub.*")
warnings.filterwarnings("ignore", module="sentence_transformers.*")

# Try to load python-dotenv
try:
    from dotenv import load_dotenv
    # Load .env from project root
    ROOT_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    ROOT_DIR = Path(__file__).resolve().parent.parent

class Config:
    ROOT_DIR = ROOT_DIR
    SOUNDS_DIR = ROOT_DIR / "Sound Effects"
    DATA_DIR = ROOT_DIR / "Databases"
    NOTES_DIR = ROOT_DIR / "Databases" / "notes"
    SCREENSHOTS_DIR = ROOT_DIR / "Databases" / "screenshots"
    MEMORY_DIR = ROOT_DIR / "Databases" / "memory"

    # Operation Mode
    OPERATION_MODE = os.getenv("OPERATION_MODE", "auto").lower()  # auto, offline, online

    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "nemotron").lower()  # ollama, nemotron, gemini, openai, groq
    LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", os.getenv("LLM_MODEL", "qwen2.5:7b"))
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    # API Keys (Cleaned of any surrounding quotes)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip().strip('"\'')
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip('"\'')
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip().strip('"\'')
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", os.getenv("NEMOTRON_API_KEY", "")).strip().strip('"\'')
    NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").strip().strip('"\'')

    # Speech / Audio
    STT_ENGINE = os.getenv("STT_ENGINE", "google").lower()  # faster-whisper, groq, google
    FASTER_WHISPER_MODEL = os.getenv("FASTER_WHISPER_MODEL", "base.en")
    TTS_ENGINE = os.getenv("TTS_ENGINE", "pyttsx3").lower()  # pyttsx3, edge-tts
    EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "en-US-ChristopherNeural")

    # Identity & Custom Nickname
    NICKNAME = os.getenv("NICKNAME", "Quadroid").strip()
    ASSISTANT_NAME = NICKNAME if NICKNAME else "Quadroid"

    # Wake-word & Voice Feedback
    WAKE_WORD = os.getenv("WAKE_WORD", ASSISTANT_NAME).lower().strip()
    WAKE_WORD_ENABLED = os.getenv("WAKE_WORD_ENABLED", "true").lower() in ("true", "1", "yes")
    ENABLE_VOICE_FEEDBACK = os.getenv("ENABLE_VOICE_FEEDBACK", "true").lower() in ("true", "1", "yes")

    # Memory & RAG
    ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() in ("true", "1", "yes")
    MEMORY_MAX_RECALL = int(os.getenv("MEMORY_MAX_RECALL", "3"))

    # GUI Settings
    GUI_THEME = os.getenv("GUI_THEME", "dark")
    GLOBAL_HOTKEY = os.getenv("GLOBAL_HOTKEY", "alt+space")

    @classmethod
    def ensure_directories(cls):
        """Ensure necessary storage directories exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.NOTES_DIR.mkdir(parents=True, exist_ok=True)
        cls.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_connected_to_internet(cls, timeout: float = 1.5) -> bool:
        """Check if machine currently has internet access."""
        try:
            # Attempt to connect to Cloudflare / Google DNS
            socket.create_connection(("1.1.1.1", 53), timeout=timeout)
            return True
        except OSError:
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=timeout)
                return True
            except OSError:
                return False

    @classmethod
    def is_offline(cls) -> bool:
        """Determine if we should run in offline mode."""
        if cls.OPERATION_MODE == "offline":
            return True
        if cls.OPERATION_MODE == "online":
            return False
        # In auto mode, check internet
        return not cls.is_connected_to_internet()

# Ensure directories exist on module load
Config.ensure_directories()
