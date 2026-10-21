import os
import json
import time
import socket
import subprocess
from typing import List, Dict, Any, Optional
from quadroid.config import Config
from quadroid.tools import TOOL_DEFINITIONS

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def is_ollama_online(timeout: float = 0.3) -> bool:
    """Quick socket check to verify if Ollama service is listening on port 11434."""
    try:
        sock = socket.create_connection(("127.0.0.1", 11434), timeout=timeout)
        sock.close()
        return True
    except OSError:
        return False


def ensure_ollama_running() -> bool:
    """
    Ensure the Ollama background daemon is actively running.
    If not running, automatically launches it in the background.
    """
    if is_ollama_online():
        return True

    app_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama app.exe")
    if os.path.exists(app_path) and hasattr(os, "startfile"):
        try:
            os.startfile(app_path)
            for _ in range(20):
                time.sleep(0.2)
                if is_ollama_online():
                    return True
        except Exception:
            pass

    ollama_candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe",
        "ollama"
    ]

    for candidate in ollama_candidates:
        try:
            if candidate == "ollama" or os.path.exists(candidate):
                creation_flags = 0x08000200 if os.name == "nt" else 0  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
                subprocess.Popen(
                    [candidate, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creation_flags
                )
                
                for _ in range(20):
                    time.sleep(0.2)
                    if is_ollama_online():
                        return True
                break
        except Exception:
            continue

    return is_ollama_online()


class LLMClient:
    """Multi-provider LLM Client supporting Google Gemini, Ollama, Groq, OpenAI, and NVIDIA."""

    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.model = Config.LLM_MODEL
        
        # If Ollama or offline mode is chosen, ensure Ollama daemon is active
        if Config.is_offline() or self.provider == "ollama":
            ensure_ollama_running()
            
        self.client = self._initialize_client()

    def _initialize_client(self) -> Optional[Any]:
        if not OPENAI_AVAILABLE:
            return None

        # Determine target provider based on settings and mode
        target_provider = (self.provider or "").lower()

        # If offline mode is forced, restrict strictly to Ollama
        if Config.is_offline():
            target_provider = "ollama"

        # Auto-detect if provider not explicitly set or set to auto
        if not target_provider or target_provider in ("auto", "default"):
            if Config.GEMINI_API_KEY:
                target_provider = "gemini"
            elif Config.GROQ_API_KEY:
                target_provider = "groq"
            elif Config.OPENAI_API_KEY:
                target_provider = "openai"
            elif Config.NVIDIA_API_KEY:
                target_provider = "nemotron"
            else:
                target_provider = "ollama"

        # 1. Google Gemini API (Ultra-Fast Cloud Reasoning)
        if target_provider == "gemini" and Config.GEMINI_API_KEY:
            self.provider = "gemini"
            if not self.model or self.model in ("llama3.2:3b", "qwen2.5:7b", "nvidia/nemotron-3-nano-30b-a3b", "gpt-4o-mini", "gemini-2.0-flash"):
                self.model = "gemini-3.6-flash"
            return OpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=Config.GEMINI_API_KEY,
                timeout=25.0,
                max_retries=2
            )

        # 2. Direct Groq API
        if target_provider == "groq" and Config.GROQ_API_KEY:
            self.provider = "groq"
            if not self.model or self.model in ("llama3.2:3b", "qwen2.5:7b", "gemini-2.0-flash"):
                self.model = "llama-3.3-70b-versatile"
            return OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=Config.GROQ_API_KEY,
                timeout=8.0,
                max_retries=1
            )

        # 3. Standard OpenAI
        if target_provider == "openai" and Config.OPENAI_API_KEY:
            self.provider = "openai"
            if not self.model or "gemini" in self.model or "llama" in self.model:
                self.model = "gpt-4o-mini"
            return OpenAI(
                api_key=Config.OPENAI_API_KEY,
                timeout=8.0,
                max_retries=1
            )

        # 4. Direct NVIDIA / Nemotron API
        if target_provider in ("nvidia", "nemotron") and Config.NVIDIA_API_KEY:
            self.provider = "nemotron"
            return OpenAI(
                base_url=Config.NVIDIA_BASE_URL,
                api_key=Config.NVIDIA_API_KEY,
                timeout=12.0,
                max_retries=1
            )

        # 5. Ollama Local Backend (Auto-starts daemon if needed)
        ensure_ollama_running()
        if is_ollama_online():
            self.provider = "ollama"
            if not self.model or "nemotron" in self.model or "gemini" in self.model or "gpt" in self.model:
                self.model = getattr(Config, "OLLAMA_MODEL", getattr(Config, "LLM_MODEL", "llama3.2:3b"))
            return OpenAI(
                base_url=getattr(Config, "OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                api_key="ollama",
                timeout=60.0,
                max_retries=1
            )

        return None

    def is_available(self) -> bool:
        """Check if an LLM client backend is ready."""
        if self.client:
            return True
        self.client = self._initialize_client()
        return self.client is not None

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Any:
        """
        Send a chat completion request with tool calling support.
        """
        if not self.is_available():
            raise ConnectionError("No LLM backend available (Ollama is not running and no Cloud API key is configured).")

        tools_param = tools if tools is not None else TOOL_DEFINITIONS
        effective_model = self.model

        try:
            response = self.client.chat.completions.create(
                model=effective_model,
                messages=messages,
                tools=tools_param if len(tools_param) > 0 else None,
                tool_choice=tool_choice if len(tools_param) > 0 else None,
                temperature=0.3,
                max_tokens=600
            )
            return response
        except Exception as e:
            if "tools" in str(e).lower() or "function" in str(e).lower():
                response = self.client.chat.completions.create(
                    model=effective_model,
                    messages=messages,
                    temperature=0.4,
                    max_tokens=500
                )
                return response
            raise e
