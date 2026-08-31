import sys
from quadroid.config import Config
from quadroid.agent import Agent
from quadroid.audio.speech import speak
from quadroid.audio.listener import listen_and_transcribe
from quadroid.audio.player import play_sound_async
from quadroid.tools.system import get_battery_status


def on_cli_action(tool_name: str, args: dict):
    args_str = ", ".join(f"{k}={v}" for k, v in args.items()) if args else ""
    print(f"\n  ⚙️  [Action Executing]: \033[96m{tool_name}({args_str})\033[0m")


def launch_cli():
    """Launch interactive Quadroid CLI session."""
    agent = Agent(on_action_callback=on_cli_action)

    is_off = Config.is_offline()
    mode_str = "\033[93mOffline (Local)\033[0m" if is_off else "\033[92mOnline\033[0m"
    bat = get_battery_status()
    bat_str = f" | Battery: {round(bat['percent'])}%" if bat.get("percent") else ""

    name = Config.ASSISTANT_NAME
    print("=" * 60)
    print(f"  🤖 \033[1m{name.upper()} 2.0 - AI Desktop Assistant\033[0m")
    print(f"  Mode: {mode_str}{bat_str} | LLM: {Config.LLM_MODEL}")
    print(f"  Type your command, or type \033[94m'voice'\033[0m to speak into mic, \033[91m'exit'\033[0m to quit.")
    print("=" * 60 + "\n")

    speak(f"{name} is ready.", async_mode=True)

    while True:
        try:
            user_input = input("\033[1;34mYou > \033[0m").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("\nGoodbye!")
                speak("Goodbye!", async_mode=False)
                break

            if user_input.lower() == "voice":
                print("\n🎤 \033[93mListening... Speak into your microphone\033[0m")
                play_sound_async("wake-up.mp3")
                transcript = listen_and_transcribe(timeout=5.0, phrase_time_limit=10.0)
                if transcript:
                    print(f"\033[1;34mYou (Voice) > \033[0m{transcript}")
                    user_input = transcript
                else:
                    print("⚠️ No speech detected.\n")
                    continue

            print("🧠 \033[90mThinking...\033[0m")
            play_sound_async("interface.mp3")
            result = agent.process_input(user_input)
            reply = result.get("response", "Done.")

            print(f"\n\033[1;32m{name} > \033[0m{reply}\n")
            if Config.ENABLE_VOICE_FEEDBACK:
                speak(reply, async_mode=True)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n\033[91mError: {str(e)}\033[0m\n")


if __name__ == "__main__":
    launch_cli()
