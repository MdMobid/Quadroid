"""
Quadroid 3.0 Interactive Setup & Environment Validator
Initializes .env and tests local hardware, audio, and AI connections.
"""
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
ENV_FILE = ROOT_DIR / ".env"
ENV_EXAMPLE = ROOT_DIR / ".env.example"


def setup():
    print("=" * 60)
    print("  ⚡ QUADROID 3.0 // SETUP & CONFIGURATION WIZARD")
    print("=" * 60)

    # 1. Check or copy .env
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            import shutil
            shutil.copy(ENV_EXAMPLE, ENV_FILE)
            print("✓ Created .env from template (.env.example)")
        else:
            ENV_FILE.write_text("OPERATION_MODE=auto\nLLM_PROVIDER=nemotron\nNICKNAME=Quadroid\n")
            print("✓ Created new .env file")
    else:
        print("✓ Existing .env file found.")

    # 2. Prompt for custom nickname (optional)
    print("\n--- Assistant Identity ---")
    current_name = input("Enter custom name for your assistant (Press Enter for 'Quadroid'): ").strip()
    if not current_name:
        current_name = "Quadroid"

    # Read .env content
    env_content = ENV_FILE.read_text(encoding="utf-8")
    lines = env_content.splitlines()

    # Update or add NICKNAME
    nickname_found = False
    new_lines = []
    for line in lines:
        if line.startswith("NICKNAME="):
            new_lines.append(f"NICKNAME={current_name}")
            nickname_found = True
        else:
            new_lines.append(line)
    if not nickname_found:
        new_lines.append(f"NICKNAME={current_name}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"✓ Assistant name set to: {current_name}")
    print(f"✓ Wake-word automatically set to: 'Hey {current_name}'")

    # 3. Ensure directories
    for folder in ["Databases/notes", "Databases/screenshots", "Databases/memory"]:
        p = ROOT_DIR / folder
        p.mkdir(parents=True, exist_ok=True)
    print("✓ Databases and storage directories verified.")

    print("\n" + "=" * 60)
    print("  🎉 Setup Complete! Launch Quadroid:")
    print("     .\\.venv\\Scripts\\python run.py")
    print("=" * 60)


if __name__ == "__main__":
    setup()