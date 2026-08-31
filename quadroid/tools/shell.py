import subprocess
from typing import Dict, Any


def run_powershell_command(command: str, timeout_seconds: int = 15) -> Dict[str, Any]:
    """
    Execute a PowerShell command on the Windows system and return the output.
    
    :param command: PowerShell command string to execute (e.g. 'Get-Process', 'ipconfig', 'Get-Date').
    :param timeout_seconds: Maximum seconds before terminating execution (default: 15).
    """
    command = command.strip()
    if not command:
        return {"success": False, "error": "Command string cannot be empty."}

    # Safety block for destructive commands
    dangerous_keywords = ["format-volume", "rmdir /s /q c:\\", "remove-item -recurse c:\\", "del /f /s /q c:\\"]
    for danger in dangerous_keywords:
        if danger in command.lower():
            return {"success": False, "error": f"Refused to execute potentially destructive command: '{command}'"}

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
