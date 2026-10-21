"""
Quadroid 3D Cyber Web HUD Server — FastAPI + WebSockets Backend
Provides high-speed real-time telemetry, 3D audio-reactive agent link,
background wake-word daemon, and desktop browser app launcher.
"""
import os
import sys
import json
import time
import asyncio
import subprocess
import webbrowser
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

from quadroid.config import Config
from quadroid.agent import Agent
from quadroid.tools.system import get_battery_status, get_system_stats
from quadroid.audio.speech import speak
from quadroid.audio.wakeword import WakeWordListener
from quadroid.audio.player import play_sound_async

# Base directories
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title=f"{Config.ASSISTANT_NAME} Cyber HUD API", version="3.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Confirmation events pending from web client
pending_confirmations: Dict[str, asyncio.Event] = {}
confirmation_responses: Dict[str, bool] = {}

# Shared agent instance
agent_instance: Optional[Agent] = None
wakeword_listener_instance: Optional[WakeWordListener] = None
main_asyncio_loop: Optional[asyncio.AbstractEventLoop] = None


def get_agent() -> Agent:
    global agent_instance
    if agent_instance is None:
        agent_instance = Agent(on_action_callback=_on_tool_action_sync)
    return agent_instance


def _broadcast_ws_message_sync(msg_dict: Dict[str, Any]):
    """Safely broadcast a JSON message to all connected WebSocket clients from any thread."""
    global main_asyncio_loop
    if main_asyncio_loop and main_asyncio_loop.is_running():
        msg_str = json.dumps(msg_dict)
        for ws in list(active_connections):
            try:
                asyncio.run_coroutine_threadsafe(ws.send_text(msg_str), main_asyncio_loop)
            except Exception:
                pass


def _on_tool_action_sync(tool_name: str, args: Dict[str, Any]):
    """Broadcast active tool execution chip to all connected web clients."""
    _broadcast_ws_message_sync({
        "type": "tool_action",
        "tool": tool_name,
        "args": args,
        "timestamp": time.time()
    })


def _on_wake_word_detected():
    """Triggered when background WakeWordListener hears 'Hey [Nickname]'."""
    print(f"\n🎤 Wake-word detected! Activating {Config.ASSISTANT_NAME}...")
    play_sound_async("wake-up.mp3")
    _broadcast_ws_message_sync({
        "type": "wake_detected",
        "timestamp": time.time()
    })


# ── Web Routes ──

@app.get("/")
async def get_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
async def api_status():
    stats = get_system_stats()
    bat = get_battery_status()
    agent = get_agent()
    mem_stats = agent.memory.get_stats() if agent.memory else {}

    return JSONResponse({
        "assistant_name": Config.ASSISTANT_NAME,
        "provider": agent.llm_client.provider,
        "model": agent.llm_client.model,
        "is_offline": Config.is_offline(),
        "wake_word_enabled": Config.WAKE_WORD_ENABLED,
        "wake_word": Config.WAKE_WORD,
        "stats": stats,
        "battery": bat,
        "memory": mem_stats
    })


@app.get("/api/memory")
async def api_memory():
    agent = get_agent()
    if not agent.memory:
        return JSONResponse({"enabled": False, "conversations": [], "profile": {}})

    recent = agent.memory.get_recent_conversations(limit=20)
    profile = agent.memory.user_profile
    stats = agent.memory.get_stats()
    return JSONResponse({
        "enabled": True,
        "stats": stats,
        "profile": profile,
        "conversations": recent
    })


# ── WebSocket Hub ──

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    agent = get_agent()

    # Send initial handshake state
    await websocket.send_text(json.dumps({
        "type": "handshake",
        "assistant_name": Config.ASSISTANT_NAME,
        "provider": agent.llm_client.provider,
        "model": agent.llm_client.model,
        "is_offline": Config.is_offline(),
        "wake_word": Config.WAKE_WORD,
        "wake_word_enabled": Config.WAKE_WORD_ENABLED
    }))

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type")

            if msg_type == "user_message":
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue

                # Notify thinking state
                await websocket.send_text(json.dumps({"type": "state", "state": "thinking"}))

                # Process asynchronously in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, agent.process_input, user_text)
                reply = result.get("response", "Task completed.")
                actions = result.get("actions", [])

                # Send speaking state FIRST so frontend completely pauses/aborts speech recognition
                await websocket.send_text(json.dumps({"type": "state", "state": "speaking"}))

                # Return response
                await websocket.send_text(json.dumps({
                    "type": "assistant_response",
                    "text": reply,
                    "actions": actions,
                    "timestamp": time.time()
                }))

                # Synchronous voice playback (blocks until TTS is completely finished)
                if Config.ENABLE_VOICE_FEEDBACK:
                    await loop.run_in_executor(None, speak, reply, False)

                # Safety buffer for speaker audio & room echo to dissipate
                await asyncio.sleep(0.6)

                # Now tell frontend speaking has finished and it is safe to idle / re-listen
                await websocket.send_text(json.dumps({"type": "state", "state": "idle"}))

            elif msg_type == "confirm_response":
                confirm_id = data.get("id")
                approved = data.get("approved", False)
                if confirm_id and confirm_id in pending_confirmations:
                    confirmation_responses[confirm_id] = approved
                    pending_confirmations[confirm_id].set()

            elif msg_type == "clear_memory":
                if agent.memory:
                    agent.memory.clear_all()
                    await websocket.send_text(json.dumps({"type": "memory_cleared"}))

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections:
            active_connections.remove(websocket)


# ── Telemetry Broadcast Loop ──

async def telemetry_broadcast_loop():
    """Broadcast real-time CPU, RAM, Battery, and Memory stats to all connected HUD clients."""
    while True:
        if active_connections:
            try:
                stats = get_system_stats()
                bat = get_battery_status()
                agent = get_agent()
                mem_count = 0
                if agent.memory:
                    m = agent.memory.get_stats()
                    mem_count = m.get("total_conversations", 0)

                payload = json.dumps({
                    "type": "telemetry",
                    "cpu": stats.get("cpu_usage_percent", 0),
                    "ram": stats.get("ram_percent", 0),
                    "ram_used_gb": round(stats.get("ram_used_gb", 0), 1),
                    "ram_total_gb": round(stats.get("ram_total_gb", 0), 1),
                    "disk": stats.get("disk_percent", 0),
                    "battery": bat.get("percent", 100),
                    "power_plugged": bat.get("power_plugged", True),
                    "memory_entries": mem_count,
                    "timestamp": time.time()
                })

                for ws in list(active_connections):
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        pass
            except Exception:
                pass
        await asyncio.sleep(2.0)


@app.on_event("startup")
async def on_startup():
    global main_asyncio_loop, wakeword_listener_instance
    main_asyncio_loop = asyncio.get_event_loop()
    asyncio.create_task(telemetry_broadcast_loop())

    # Start background wake-word listener if enabled
    if Config.WAKE_WORD_ENABLED:
        try:
            wakeword_listener_instance = WakeWordListener(on_wake_detected=_on_wake_word_detected)
            wakeword_listener_instance.start()
            print(f"👂 Background Wake-Word listener started for '{Config.WAKE_WORD}'.")
        except Exception as e:
            print(f"⚠️ Could not initialize background wake-word listener: {e}")


# ── Launcher ──

def launch_browser_app(url: str):
    """Launch the HUD in borderless Native Chrome/Edge App Mode."""
    time.sleep(1.2)
    # 1. Try Chrome App mode
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for p in chrome_paths:
        if os.path.exists(p):
            subprocess.Popen([p, f"--app={url}", "--window-size=1100,780", "--window-position=center"])
            return

    # 2. Try Edge App mode
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    for p in edge_paths:
        if os.path.exists(p):
            subprocess.Popen([p, f"--app={url}", "--window-size=1100,780", "--window-position=center"])
            return

    # 3. Default browser fallback
    webbrowser.open(url)


def run_web_hud(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    """Start the Cyber Web HUD server and launch the desktop window."""
    url = f"http://{host}:{port}"
    print("=" * 60)
    print(f"  🌌 QUADROID 3.0")
    print(f"  ⚡ Live URL: {url}")
    print(f"  🎙️ Wake-Word: 'Hey {Config.ASSISTANT_NAME}'")
    print("=" * 60)

    if open_browser:
        threading.Thread(target=launch_browser_app, args=(url,), daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    run_web_hud()
