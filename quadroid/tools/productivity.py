import os
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from quadroid.config import Config

# Clipboard
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# Image grab for screenshots
try:
    from PIL import ImageGrab
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False


def take_screenshot(filename: str = None) -> Dict[str, Any]:
    """
    Capture a screenshot of the computer screen and save it.
    
    :param filename: Optional custom filename for the screenshot.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not filename:
        filename = f"screenshot_{timestamp}.png"
    elif not filename.endswith((".png", ".jpg", ".jpeg")):
        filename = f"{filename}.png"

    save_path = Config.SCREENSHOTS_DIR / filename

    # 1. Try Pillow ImageGrab
    if SCREENSHOT_AVAILABLE:
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            screenshot.save(save_path)
            return {
                "success": True,
                "message": f"Screenshot saved at {save_path.name}",
                "file_path": str(save_path)
            }
        except Exception:
            pass

    # 2. Fallback to native Windows PowerShell Screen Capture
    try:
        ps_cmd = f"""
        Add-Type -AssemblyName System.Windows.Forms;
        Add-Type -AssemblyName System.Drawing;
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds;
        $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height;
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap);
        $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size);
        $bitmap.Save('{str(save_path)}');
        $graphics.Dispose();
        $bitmap.Dispose();
        """
        subprocess.run(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        if save_path.exists():
            return {
                "success": True,
                "message": f"Screenshot saved at {save_path.name}",
                "file_path": str(save_path)
            }
    except Exception as e:
        return {"success": False, "error": f"Screenshot capture error: {str(e)}"}

    return {"success": False, "error": "Could not capture screenshot."}


def get_clipboard_content() -> Dict[str, Any]:
    """Read the current text from the Windows clipboard."""
    if not CLIPBOARD_AVAILABLE:
        return {"success": False, "error": "Clipboard module unavailable (pyperclip required)."}
    try:
        text = pyperclip.paste()
        return {
            "success": True,
            "content": text,
            "preview": (text[:100] + "...") if len(text) > 100 else text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_clipboard_content(text: str) -> Dict[str, Any]:
    """
    Copy text to the Windows clipboard.
    
    :param text: Text string to copy to clipboard.
    """
    if not CLIPBOARD_AVAILABLE:
        return {"success": False, "error": "Clipboard module unavailable."}
    try:
        pyperclip.copy(text)
        return {"success": True, "message": "Text copied to clipboard."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_note(title: str, content: str) -> Dict[str, Any]:
    """
    Save a quick text note or reminder locally.
    
    :param title: Short title or subject of the note.
    :param content: Content body of the note.
    """
    try:
        clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
        if not clean_title:
            clean_title = f"note_{int(time.time())}"
            
        note_file = Config.NOTES_DIR / f"{clean_title}.txt"
        with open(note_file, "w", encoding="utf-8") as f:
            f.write(f"Title: {title}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}\n")

        return {
            "success": True,
            "message": f"Note '{title}' saved successfully.",
            "file_path": str(note_file)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_notes() -> Dict[str, Any]:
    """List all saved personal notes."""
    try:
        notes = []
        for file in Config.NOTES_DIR.glob("*.txt"):
            notes.append(file.stem)
        return {"success": True, "notes": notes}
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_note(title: str) -> Dict[str, Any]:
    """
    Read the contents of a saved note by title.
    
    :param title: Title or name of the note to read.
    """
    try:
        clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
        note_file = Config.NOTES_DIR / f"{clean_title}.txt"
        if not note_file.exists():
            candidates = list(Config.NOTES_DIR.glob(f"*{clean_title}*.txt"))
            if candidates:
                note_file = candidates[0]
            else:
                return {"success": False, "error": f"Note '{title}' not found."}
                
        with open(note_file, "r", encoding="utf-8") as f:
            content = f.read()

        return {"success": True, "title": note_file.stem, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}
