import sys
import argparse
import os

from quadroid.config import Config


def main():
    parser = argparse.ArgumentParser(description="Quadroid 2.0 - AI Desktop Assistant")
    parser.add_argument("--cli", action="store_true", help="Launch interactive CLI terminal mode")
    parser.add_argument("--offline", action="store_true", help="Force 100% offline mode with Ollama")
    parser.add_argument("--voice-only", action="store_true", help="Run background voice & wake-word daemon")
    
    args = parser.parse_args()

    if args.offline:
        Config.OPERATION_MODE = "offline"

    print("=" * 60)
    print("  🚀 Initializing Quadroid 2.0 AI Assistant...")
    print(f"  Mode: {'Offline' if Config.is_offline() else 'Online'} | LLM: {Config.LLM_PROVIDER}")
    print("=" * 60)

    if args.cli:
        from quadroid.ui.cli import launch_cli
        launch_cli()
    elif args.voice_only:
        from quadroid.agent import Agent
        from quadroid.audio.wakeword import WakeWordListener
        from quadroid.audio.listener import listen_and_transcribe
        from quadroid.audio.speech import speak
        import time

        agent = Agent()
        print("👂 Wake word active. Say 'Hey Quadroid' to interact...")
        speak("Quadroid background service is active.", async_mode=True)

        def on_wake():
            print("\n🎤 Wake word detected! Listening for instruction...")
            transcript = listen_and_transcribe(timeout=5.0, phrase_time_limit=10.0)
            if transcript:
                print(f"You: {transcript}")
                result = agent.process_input(transcript)
                reply = result.get("response", "Done.")
                print(f"Quadroid: {reply}")
                speak(reply, async_mode=False)

        listener = WakeWordListener(on_wake_detected=on_wake)
        listener.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting voice daemon...")
    else:
        # Default: Launch GUI Desktop App
        from quadroid.ui.gui import launch_gui
        launch_gui()


if __name__ == "__main__":
    main()
