# 🤖 Quadroid 2.0: AI Desktop Assistant for Windows

<div align="center">

**Next-Gen Voice-Activated Desktop & Laptop Personal Assistant**  
*Control your PC, automate daily workflows, and execute tasks — both Online and 100% Offline.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Offline Capable](https://img.shields.io/badge/Offline-100%25%20Capable%20(Ollama)-brightgreen.svg)]()

</div>

---

## 🌟 Key Features

- 🔒 **100% Offline Mode (No Internet Required)**: Runs locally with **Ollama** (`llama3.2:3b` / `qwen2.5:3b`), local speech recognition (**`faster-whisper`**), and offline Windows SAPI5 voice (**`pyttsx3`**).
- 🌐 **Multi-Provider Cloud Support**: Seamlessly switch to **Google Gemini**, **Groq** (ultra-fast 500+ tokens/s), or **OpenAI** (GPT-4o) with one line in `.env`.
- 👂 **Background Wake-Word Detection**: Say `"Hey Quadroid"` or `"Quadroid"` anytime to wake up the assistant without touching the keyboard.
- 🖥️ **Modern Desktop GUI**: Sleek dark-mode floating app with real-time tool execution chips, animated voice orb, and dual voice/text inputs.
- ⚙️ **Windows Automation Suite (Function Calling)**:
  - **Hardware Control**: Master volume control, mute/unmute (`pycaw`), screen brightness (`screen_brightness_control`), battery & charging stats (`psutil`), screen lock (`Win+L`), sleep.
  - **App & Process Management**: Open and close any desktop application or process (`AppOpener` / `psutil`).
  - **Productivity**: Save & read personal notes, read/write clipboard (`pyperclip`), instant desktop screenshot capture.
  - **File Explorer**: Search files across user directories and locate them in Windows Explorer.
  - **Web & Live Info**: Instant live weather (free, no API key needed), top news headlines, Google search, YouTube & URL opener.
  - **Safe Shell Runner**: PowerShell automation for diagnostic commands.

---

## 🚀 Quick Start

### 1. Clone & Set Up Virtual Environment

```powershell
# Navigate to Quadroid directory
cd d:\GitHub\Quadroid

# Create local virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Settings (`.env`)

Copy the template configuration:
```powershell
copy .env.example .env
```

Edit `.env` to configure your preferred mode:
- **For 100% Offline Use (Ollama)**:
  1. Install [Ollama](https://ollama.com/) and run: `ollama run llama3.2:3b`
  2. Set `LLM_PROVIDER=ollama` in `.env`.
- **For NVIDIA Nemotron (e.g. `nvidia/nemotron-3-nano-30b-a3b`)**:
  - Set `LLM_PROVIDER=nemotron` and `LLM_MODEL=nvidia/nemotron-3-nano-30b-a3b`.
  - Add your `NVIDIA_API_KEY` (from [NVIDIA Build](https://build.nvidia.com/)).
- **For Free Cloud Speed (Gemini / Groq)**:
  - Set `LLM_PROVIDER=gemini` and add your `GEMINI_API_KEY`, or set `LLM_PROVIDER=groq` with `GROQ_API_KEY`.
- **For OpenAI**:
  - Set `LLM_PROVIDER=openai` and add your `OPENAI_API_KEY`.

---

## 🎮 Running Quadroid

### 🖥️ 1. Launch Modern Desktop GUI (Default)
```powershell
.\.venv\Scripts\python run.py
```
*Brings up the floating dark-mode app with voice orb, chat history, and background wake-word listener.*

### 💻 2. Launch Interactive Terminal CLI Mode
```powershell
.\.venv\Scripts\python run.py --cli
```
*Fast text/voice terminal interface with live tool execution tracing.*

### 🔒 3. Force 100% Offline Mode
```powershell
.\.venv\Scripts\python run.py --offline
```

### 🎙️ 4. Run Background Voice Daemon Only
```powershell
.\.venv\Scripts\python run.py --voice-only
```

---

## 🛠️ Example Commands

You can speak or type natural commands such as:
- *"Set volume to 40% and check my battery"*
- *"Mute system audio"*
- *"Take a screenshot"*
- *"Open Notepad and save a note 'Meeting at 3 PM'"*
- *"Search for Python files in my Documents"*
- *"What is the weather in London right now?"*
- *"Close Chrome and open VS Code"*
- *"Lock my screen"*

---

## 📁 Project Structure

```
Quadroid/
├── .env.example              # Configuration template
├── requirements.txt          # Modern Python dependencies
├── run.py                    # Main launcher (GUI / CLI / Voice)
├── main.py                   # Legacy entry point forwarder
├── quadroid/
│   ├── config.py             # Settings & auto-offline detector
│   ├── agent.py              # LLM agent & tool dispatcher
│   ├── core/
│   │   ├── llm.py            # Multi-provider client (Ollama/Gemini/OpenAI/Groq)
│   │   └── prompts.py        # System persona & instructions
│   ├── audio/
│   │   ├── speech.py         # TTS (pyttsx3 offline + edge-tts online)
│   │   ├── listener.py       # STT (faster-whisper offline + cloud fallback)
│   │   ├── wakeword.py       # Background 'Hey Quadroid' wake detector
│   │   └── player.py         # Async sound cues
│   ├── tools/
│   │   ├── __init__.py       # Tool registry & function schemas
│   │   ├── system.py         # Volume, brightness, battery, power
│   │   ├── apps.py           # Launch, close, list applications
│   │   ├── productivity.py   # Screenshots, clipboard, notes
│   │   ├── files.py          # File search & explorer
│   │   ├── web.py            # Search, weather, news
│   │   └── shell.py          # Safe PowerShell execution
│   └── ui/
│       ├── gui.py            # CustomTkinter modern dark GUI
│       └── cli.py            # Rich terminal chat interface
└── Sound Effects/            # Audio cue assets
```

---

## 📄 License & Credits

- Licensed under [GNU Affero General Public License v3](LICENSE).
- Created with ❤️ by [Md Mobid](https://github.com/MdMobid).