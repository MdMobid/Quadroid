import sys
import argparse
import os

from quadroid.config import Config


def main():
    parser = argparse.ArgumentParser(description="Quadroid 3.0 - AI Assistant")
    parser.add_argument("--cli", action="store_true", help="Launch interactive CLI terminal mode")
    parser.add_argument("--gui", "--desktop", action="store_true", help="Launch CustomTkinter desktop window")
    parser.add_argument("--port", type=int, default=8000, help="Web HUD port (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Web HUD host (default: 127.0.0.1)")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-launch browser window")
    parser.add_argument("--offline", action="store_true", help="Force 100% offline mode with Ollama")
    parser.add_argument("--voice-only", action="store_true", help="Run background voice & wake-word daemon")
    
    args = parser.parse_args()

    if args.offline:
        Config.OPERATION_MODE = "offline"

    # Auto-start Ollama if offline mode or Ollama provider is selected
    if Config.is_offline() or Config.LLM_PROVIDER == "ollama":
        from quadroid.core.llm import ensure_ollama_running
        if ensure_ollama_running():
            print("  ⚡ Ollama local AI engine is running & ready.")
        else:
            print("  ⚠️ Ollama is not installed or failed to start. Falling back to local rules.")

    print("=" * 60)
    print(f"  🌌 Initializing Quadroid 3.0 AI Assistant ({Config.ASSISTANT_NAME})...")
    print(f"  Mode: {'Offline' if Config.is_offline() else 'Online'} | LLM: {Config.LLM_PROVIDER}")
    print("=" * 60)

    if args.cli:
        from quadroid.ui.cli import launch_cli
        launch_cli()
    elif args.gui:
        from quadroid.ui.gui import launch_gui
        launch_gui()
    elif args.voice_only:
        from quadroid.agent import Agent
        from quadroid.audio.wakeword import WakeWordListener
        from quadroid.audio.listener import listen_and_transcribe
        from quadroid.audio.speech import speak
        import time

        agent = Agent()
        print(f"👂 Wake word active. Say 'Hey {Config.ASSISTANT_NAME}' to interact...")
        speak(f"{Config.ASSISTANT_NAME} background service is active.", async_mode=True)

        def on_wake():
            print("\n🎤 Wake word detected! Listening for instruction...")
            transcript = listen_and_transcribe(timeout=5.0, phrase_time_limit=10.0)
            if transcript:
                print(f"You: {transcript}")
                result = agent.process_input(transcript)
                reply = result.get("response", "Done.")
                print(f"{Config.ASSISTANT_NAME}: {reply}")
                speak(reply, async_mode=False)

        listener = WakeWordListener(on_wake_detected=on_wake)
        listener.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting voice daemon...")
    else:
        # Default: Launch 3D Holographic Cyber Web HUD on Localhost
        from quadroid.web.server import run_web_hud
        run_web_hud(host=args.host, port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
