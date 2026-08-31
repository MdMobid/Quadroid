import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List


def search_files(query: str, root_path: str = None, max_results: int = 15) -> Dict[str, Any]:
    """
    Search for files or folders matching a query name across the user profile or specific directory.
    
    :param query: File name or pattern to search for (e.g. 'resume.pdf', 'report', '*.py').
    :param root_path: Optional starting directory path (default: user home folder).
    :param max_results: Maximum matches to return (default: 15).
    """
    query = query.lower().strip()
    if not query:
        return {"success": False, "error": "Search query cannot be empty."}

    if not root_path:
        root_path = os.path.expanduser("~")
    
    search_root = Path(root_path)
    if not search_root.exists():
        return {"success": False, "error": f"Path '{root_path}' does not exist."}

    matches = []
    # Avoid scanning deep hidden/system folders
    ignored_dirs = {".git", ".venv", "node_modules", "appdata", "$recycle.bin"}

    try:
        for root, dirs, files in os.walk(search_root):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d.lower() not in ignored_dirs and not d.startswith(".")]

            for file in files:
                if query in file.lower():
                    full_path = os.path.join(root, file)
                    matches.append(full_path)
                    if len(matches) >= max_results:
                        break
            if len(matches) >= max_results:
                break

        return {
            "success": True,
            "query": query,
            "total_found": len(matches),
            "files": matches
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def open_path_in_explorer(path: str) -> Dict[str, Any]:
    """
    Open a file or folder path in Windows File Explorer.
    
    :param path: Absolute or relative file/folder path to open.
    """
    target = Path(path).resolve()
    if not target.exists():
        return {"success": False, "error": f"Path '{path}' does not exist."}

    try:
        if target.is_dir():
            os.startfile(str(target))
        else:
            # Select file in Explorer
            subprocess.run(["explorer", f"/select,{str(target)}"])
        return {"success": True, "message": f"Opened '{target}' in File Explorer."}
    except Exception as e:
        return {"success": False, "error": str(e)}
