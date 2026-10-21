"""
Quadroid File Operation Tools — Create, delete, move, copy, rename files & folders.
Destructive operations require user confirmation via popup dialog.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any

from quadroid.ui.confirm import request_confirmation


def delete_file(path: str) -> Dict[str, Any]:
    """
    Delete a file or folder. Requires user confirmation.

    :param path: Absolute path to the file or folder to delete.
    """
    target = Path(path).resolve()
    if not target.exists():
        return {"success": False, "error": f"Path '{path}' does not exist."}

    item_type = "folder" if target.is_dir() else "file"
    display_name = target.name
    display_path = str(target)

    approved = request_confirmation(
        title=f"Delete {item_type.title()}",
        message=f"Are you sure you want to permanently delete this {item_type}?\n\n{display_name}\n📁 {display_path}",
        action_type="danger"
    )

    if not approved:
        return {"success": False, "error": "Action cancelled by user.", "cancelled": True}

    try:
        if target.is_dir():
            shutil.rmtree(str(target))
        else:
            target.unlink()
        return {"success": True, "message": f"Deleted {item_type}: {display_path}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to delete: {str(e)}"}


def move_file(source: str, destination: str) -> Dict[str, Any]:
    """
    Move a file or folder to a new location. Requires user confirmation.

    :param source: Source file or folder path.
    :param destination: Destination path.
    """
    src = Path(source).resolve()
    dst = Path(destination).resolve()

    if not src.exists():
        return {"success": False, "error": f"Source '{source}' does not exist."}

    approved = request_confirmation(
        title="Move File",
        message=f"Move this item?\n\nFrom: {src}\nTo: {dst}",
        action_type="warning"
    )

    if not approved:
        return {"success": False, "error": "Action cancelled by user.", "cancelled": True}

    try:
        shutil.move(str(src), str(dst))
        return {"success": True, "message": f"Moved '{src.name}' to '{dst}'"}
    except Exception as e:
        return {"success": False, "error": f"Failed to move: {str(e)}"}


def copy_file(source: str, destination: str) -> Dict[str, Any]:
    """
    Copy a file or folder to a destination. Non-destructive — no confirmation needed.

    :param source: Source file or folder path.
    :param destination: Destination path.
    """
    src = Path(source).resolve()
    dst = Path(destination).resolve()

    if not src.exists():
        return {"success": False, "error": f"Source '{source}' does not exist."}

    try:
        if src.is_dir():
            shutil.copytree(str(src), str(dst))
        else:
            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
        return {"success": True, "message": f"Copied '{src.name}' to '{dst}'"}
    except Exception as e:
        return {"success": False, "error": f"Failed to copy: {str(e)}"}


def rename_file(path: str, new_name: str) -> Dict[str, Any]:
    """
    Rename a file or folder. Requires user confirmation.

    :param path: Path to the file or folder to rename.
    :param new_name: New name for the file or folder (just the name, not full path).
    """
    target = Path(path).resolve()
    if not target.exists():
        return {"success": False, "error": f"Path '{path}' does not exist."}

    new_path = target.parent / new_name

    approved = request_confirmation(
        title="Rename",
        message=f"Rename this item?\n\nFrom: {target.name}\nTo: {new_name}",
        action_type="warning"
    )

    if not approved:
        return {"success": False, "error": "Action cancelled by user.", "cancelled": True}

    try:
        target.rename(new_path)
        return {"success": True, "message": f"Renamed '{target.name}' to '{new_name}'"}
    except Exception as e:
        return {"success": False, "error": f"Failed to rename: {str(e)}"}


def create_folder(path: str) -> Dict[str, Any]:
    """
    Create a new directory. Non-destructive — no confirmation needed.

    :param path: Absolute path of the new directory to create.
    """
    target = Path(path).resolve()

    if target.exists():
        return {"success": True, "message": f"Folder already exists: {target}"}

    try:
        target.mkdir(parents=True, exist_ok=True)
        return {"success": True, "message": f"Created folder: {target}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to create folder: {str(e)}"}
