"""
Quadroid Shell Tool — Execute PowerShell commands with user confirmation popup.
"""
import subprocess
from typing import Dict, Any

from quadroid.ui.confirm import request_confirmation


def run_powershell_command(command: str, timeout_seconds: int = 15) -> Dict[str, Any]:
    """
    Execute a PowerShell command on the Windows system and return the output.
    All commands require user confirmation before execution.

    :param command: PowerShell command string to execute (e.g. 'Get-Process', 'ipconfig', 'Get-Date').
    :param timeout_seconds: Maximum seconds before terminating execution (default: 15).
    """
    command = command.strip()
    if not command:
        return {"success": False, "error": "Command string cannot be empty."}

    # Hard block for catastrophic commands
    catastrophic = ["format-volume", "rmdir /s /q c:\\", "remove-item -recurse c:\\", "del /f /s /q c:\\"]
    for danger in catastrophic:
        if danger in command.lower():
            return {"success": False, "error": f"Refused to execute catastrophic command: '{command}'"}

    # Request user confirmation with the exact command shown
    approved = request_confirmation(
        title="Execute Shell Command",
        message=f"Quadroid wants to run this command:\n\n> {command}",
        action_type="warning"
    )

    if not approved:
        return {"success": False, "error": "Command execution cancelled by user.", "cancelled": True}

    try:
        process = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        stdout = process.stdout.strip()
        stderr = process.stderr.strip()

        return {
            "success": process.returncode == 0,
            "return_code": process.returncode,
            "output": stdout if stdout else (stderr if stderr else "Command executed with no output."),
            "error": stderr if process.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout_seconds} seconds."}
    except Exception as e:
        return {"success": False, "error": str(e)}
