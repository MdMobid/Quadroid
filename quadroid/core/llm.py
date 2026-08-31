import json
import socket
from typing import List, Dict, Any, Optional
from quadroid.config import Config
from quadroid.tools import TOOL_DEFINITIONS

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def is_ollama_online(timeout: float = 0.2) -> bool:
    """Quick socket check to verify if Ollama service is listening on port 11434."""
    try:
        sock = socket.create_connection(("127.0.0.1", 11434), timeout=timeout)
        sock.close()
        return True
    except OSError:
        return False


class LLMClient:
    """Multi-provider LLM Client supporting NVIDIA Nemotron, Ollama, OpenAI, Groq, and Gemini."""

    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.model = Config.LLM_MODEL
        self.client = self._initialize_client()

    def _initialize_client(self) -> Optional[Any]:
        if not OPENAI_AVAILABLE:
            return None

        # 1. Direct NVIDIA / Nemotron API
        if (self.provider in ("nvidia", "nemotron") or Config.NVIDIA_API_KEY) and Config.NVIDIA_API_KEY:
            if not is_ollama_online() or self.provider in ("nvidia", "nemotron"):
                self.provider = "nemotron"
                if self.model in ("llama3.2:3b", "gpt-4o-mini", ""):
                    self.model = "nvidia/nemotron-3-nano-30b-a3b"
                return OpenAI(
                    base_url=Config.NVIDIA_BASE_URL,
                    api_key=Config.NVIDIA_API_KEY,
                    timeout=12.0,
                    max_retries=1
                )

        # 2. Direct Groq
        if self.provider == "groq" and Config.GROQ_API_KEY:
            return OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=Config.GROQ_API_KEY,
                timeout=8.0,
                max_retries=1
            )

        # 3. Direct Gemini
        elif self.provider == "gemini" and Config.GEMINI_API_KEY:
            return OpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=Config.GEMINI_API_KEY,
                timeout=8.0,
                max_retries=1
            )

        # 4. Standard OpenAI
        elif self.provider == "openai" and Config.OPENAI_API_KEY:
            return OpenAI(
                api_key=Config.OPENAI_API_KEY,
                timeout=8.0,
                max_retries=1
            )

        # 5. Ollama (Only connect if Ollama port is actively listening)
        if is_ollama_online():
            return OpenAI(
                base_url=Config.OLLAMA_BASE_URL,
                api_key="ollama",
                timeout=5.0,
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
                temperature=0.4,
                max_tokens=500
            )
            return response
        except Exception as e:
            if "tools" in str(e).lower() or "function" in str(e).lower():
                response = self.client.chat.completions.create(
                    model=effective_model,
                    messages=messages,
                    temperature=0.5,
                    max_tokens=400
                )
                return response
            raise e
