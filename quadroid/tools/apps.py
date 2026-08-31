import os
import sys
import io
import subprocess
import psutil
from typing import Dict, Any, List


def _get_appopener():
    """Safely import AppOpener without printing startup noise to terminal."""
    try:
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        from AppOpener import open as app_open, close as app_close
        sys.stdout = old_stdout
        return app_open, app_close
    except Exception:
        sys.stdout = old_stdout
        return None, None


def open_application(app_name: str) -> Dict[str, Any]:
    """
    Launch or open an application on Windows (e.g. 'chrome', 'notepad', 'calculator', 'spotify', 'code', 'explorer', 'settings').
    
    :param app_name: Name of the application to launch.
    """
    app_name = app_name.strip()
    if not app_name:
        return {"success": False, "error": "Application name cannot be empty."}

    # Common Windows app aliases
    app_map = {
        "calculator": "calc",
        "command prompt": "cmd",
        "terminal": "wt",
        "file explorer": "explorer",
        "explorer": "explorer",
        "task manager": "taskmgr",
        "settings": "ms-settings:",
        "edge": "msedge",
        "vs code": "code",
        "visual studio code": "code",
        "paint": "mspaint",
        "notepad": "notepad",
    }
    
    clean_name = app_map.get(app_name.lower(), app_name)
    
    # 1. Try Windows start protocol
    try:
        if clean_name.startswith("ms-") or clean_name in ["calc", "notepad", "mspaint", "taskmgr", "explorer", "cmd", "wt", "code"]:
            subprocess.Popen(["cmd", "/c", "start", "", clean_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "message": f"Opened {app_name}."}
    except Exception:
        pass

    # 2. Try AppOpener if available
    app_open, _ = _get_appopener()
    if app_open:
        try:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            app_open(app_name, match_closest=True, output=False)
            sys.stdout = old_stdout
            return {"success": True, "message": f"Launched {app_name}."}
        except Exception:
            sys.stdout = old_stdout

    # 3. Fallback to start command via shell
    try:
        subprocess.Popen(["cmd", "/c", "start", "", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True, "message": f"Attempted to open {app_name}."}
    except Exception as e:
        return {"success": False, "error": f"Failed to open {app_name}: {str(e)}"}


def close_application(app_name: str) -> Dict[str, Any]:
    """
    Close or terminate a running application on Windows by name.
    
    :param app_name: Name of the application or process to close (e.g. 'chrome', 'notepad', 'spotify').
    """
    app_name = app_name.lower().strip()
    if not app_name:
        return {"success": False, "error": "Application name cannot be empty."}

    closed_count = 0
    terminated_processes = []

    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = proc.info['name'].lower()
                pname_clean = pname.replace(".exe", "")
                if app_name in pname_clean or pname_clean in app_name:
                    proc.terminate()
                    closed_count += 1
                    terminated_processes.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        return {"success": False, "error": str(e)}

    if closed_count > 0:
        return {
            "success": True, 
            "message": f"Closed {closed_count} instance(s) of {app_name}.",
            "processes": list(set(terminated_processes))
        }
    else:
        try:
            exe_target = app_name if app_name.endswith(".exe") else f"{app_name}.exe"
            subprocess.run(["taskkill", "/F", "/IM", exe_target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "message": f"Closed {app_name}."}
        except Exception:
            return {"success": False, "message": f"No running application matching '{app_name}' was found."}


def list_running_apps() -> Dict[str, Any]:
    """List names of currently running user applications and processes."""
    apps = set()
    try:
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name and not name.startswith("System") and not name.startswith("svchost"):
                    apps.add(name.replace(".exe", ""))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"success": True, "running_apps": sorted(list(apps))[:40]}
    except Exception as e:
        return {"success": False, "error": str(e)}
