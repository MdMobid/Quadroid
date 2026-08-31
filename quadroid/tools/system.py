import os
import ctypes
import psutil
from typing import Dict, Any, Union

# Attempt pycaw import for Windows Volume control
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

# Attempt screen brightness import
try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    SBC_AVAILABLE = False


def _get_audio_endpoint():
    """Helper to retrieve Windows master audio endpoint (supports modern and legacy pycaw)."""
    if not PYCAW_AVAILABLE:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        if hasattr(devices, "EndpointVolume") and devices.EndpointVolume:
            return devices.EndpointVolume
        if hasattr(devices, "Activate"):
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
    except Exception:
        return None
    return None


def get_system_volume() -> Dict[str, Any]:
    """Get current master audio volume percentage and mute status."""
    volume_endpoint = _get_audio_endpoint()
    if volume_endpoint:
        try:
            current_vol = round(volume_endpoint.GetMasterVolumeLevelScalar() * 100)
            is_muted = bool(volume_endpoint.GetMute())
            return {"success": True, "volume": current_vol, "muted": is_muted}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "Volume control is unavailable (pycaw required)."}


def set_system_volume(level: int) -> Dict[str, Any]:
    """
    Set master audio volume level (0 to 100).
    
    :param level: Desired volume from 0 to 100.
    """
    level = max(0, min(100, int(level)))
    volume_endpoint = _get_audio_endpoint()
    if volume_endpoint:
        try:
            volume_endpoint.SetMasterVolumeLevelScalar(level / 100.0, None)
            if volume_endpoint.GetMute() and level > 0:
                volume_endpoint.SetMute(0, None)
            return {"success": True, "message": f"Volume set to {level}%", "volume": level}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "Volume control is unavailable."}


def mute_system_volume(mute: bool = True) -> Dict[str, Any]:
    """
    Mute or unmute system audio.
    
    :param mute: True to mute, False to unmute.
    """
    volume_endpoint = _get_audio_endpoint()
    if volume_endpoint:
        try:
            volume_endpoint.SetMute(1 if mute else 0, None)
            state = "muted" if mute else "unmuted"
            return {"success": True, "message": f"System audio {state}."}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "Volume control is unavailable."}


def get_screen_brightness() -> Dict[str, Any]:
    """Get current display brightness percentage."""
    if SBC_AVAILABLE:
        try:
            brightness = sbc.get_brightness()
            current = brightness[0] if isinstance(brightness, list) else brightness
            return {"success": True, "brightness": current}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "Brightness control is unavailable (screen_brightness_control required)."}


def set_screen_brightness(level: int) -> Dict[str, Any]:
    """
    Set display brightness percentage (0 to 100).
    
    :param level: Target brightness percentage (0 - 100).
    """
    level = max(0, min(100, int(level)))
    if SBC_AVAILABLE:
        try:
            sbc.set_brightness(level)
            return {"success": True, "message": f"Brightness set to {level}%", "brightness": level}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "Brightness control is unavailable."}


def get_battery_status() -> Dict[str, Any]:
    """Get laptop battery percentage and charging status."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return {"success": True, "battery": None, "message": "No battery detected (Desktop PC or unsupported hardware)."}
        
        return {
            "success": True,
            "percent": round(battery.percent, 1),
            "power_plugged": battery.power_plugged,
            "secsleft": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unlimited (Plugged In)",
            "message": f"Battery is at {round(battery.percent)}% ({'Plugged In / Charging' if battery.power_plugged else 'Discharging'})"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_system_stats() -> Dict[str, Any]:
    """Get current CPU, RAM, and Disk resource utilization stats."""
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')
        
        return {
            "success": True,
            "cpu_usage_percent": cpu_usage,
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "ram_total_gb": round(ram.total / (1024**3), 2),
            "ram_percent": ram.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "message": f"CPU: {cpu_usage}%, RAM: {ram.percent}% ({round(ram.used/(1024**3), 1)}GB / {round(ram.total/(1024**3), 1)}GB)"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def lock_workstation() -> Dict[str, Any]:
    """Lock the Windows workstation screen."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return {"success": True, "message": "Workstation locked successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}
