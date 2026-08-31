import json
from typing import Dict, Any, Callable, List

# Import all tool functions
from quadroid.tools.system import (
    get_system_volume,
    set_system_volume,
    mute_system_volume,
    get_screen_brightness,
    set_screen_brightness,
    get_battery_status,
    get_system_stats,
    lock_workstation
)
from quadroid.tools.apps import (
    open_application,
    close_application,
    list_running_apps
)
from quadroid.tools.productivity import (
    take_screenshot,
    get_clipboard_content,
    set_clipboard_content,
    save_note,
    list_notes,
    read_note
)
from quadroid.tools.files import (
    search_files,
    open_path_in_explorer
)
from quadroid.tools.web import (
    open_url,
    web_search,
    get_weather,
    get_latest_news
)
from quadroid.tools.shell import (
    run_powershell_command
)

# Registry mapping tool name -> Python callable
TOOL_REGISTRY: Dict[str, Callable] = {
    "get_system_volume": get_system_volume,
    "set_system_volume": set_system_volume,
    "mute_system_volume": mute_system_volume,
    "get_screen_brightness": get_screen_brightness,
    "set_screen_brightness": set_screen_brightness,
    "get_battery_status": get_battery_status,
    "get_system_stats": get_system_stats,
    "lock_workstation": lock_workstation,
    "open_application": open_application,
    "close_application": close_application,
    "list_running_apps": list_running_apps,
    "take_screenshot": take_screenshot,
    "get_clipboard_content": get_clipboard_content,
    "set_clipboard_content": set_clipboard_content,
    "save_note": save_note,
    "list_notes": list_notes,
    "read_note": read_note,
    "search_files": search_files,
    "open_path_in_explorer": open_path_in_explorer,
    "open_url": open_url,
    "web_search": web_search,
    "get_weather": get_weather,
    "get_latest_news": get_latest_news,
    "run_powershell_command": run_powershell_command,
}

# OpenAI & Ollama function calling tool specifications
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_system_volume",
            "description": "Get the current master audio volume percentage and mute status on Windows.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_volume",
            "description": "Set the master audio volume level (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Target volume percentage from 0 to 100"}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mute_system_volume",
            "description": "Mute or unmute system audio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mute": {"type": "boolean", "description": "True to mute, False to unmute"}
                },
                "required": ["mute"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_screen_brightness",
            "description": "Get current display screen brightness level.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_screen_brightness",
            "description": "Set display screen brightness level (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Target brightness percentage (0 - 100)"}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_battery_status",
            "description": "Get laptop battery charge percentage and power plugged-in status.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_stats",
            "description": "Get CPU usage, RAM memory consumption, and disk storage stats.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lock_workstation",
            "description": "Lock the Windows workstation screen.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Launch or open a desktop application (e.g., 'notepad', 'chrome', 'calculator', 'vs code', 'spotify', 'task manager').",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to open"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Close or terminate a running desktop application or process by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to close"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_running_apps",
            "description": "List currently running user applications and processes.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Capture a screenshot of the computer screen and save it locally.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Optional custom filename"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard_content",
            "description": "Get current copied text from the Windows clipboard.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard_content",
            "description": "Copy text string to the Windows clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to copy to clipboard"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Save a quick personal text note or reminder locally.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short title of the note"},
                    "content": {"type": "string", "description": "Body content of the note"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "List all saved personal notes.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_note",
            "description": "Read the contents of a saved note by title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of note to read"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files and directories on the computer matching a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "File or folder name pattern to search for"},
                    "root_path": {"type": "string", "description": "Optional directory path to search within"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_path_in_explorer",
            "description": "Open a specific file or folder in Windows File Explorer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File or folder path to open"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a website, YouTube video, or URL in the web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search Google or the web for answers, topics, or sites.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current live weather forecast for a city or current location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, or empty for local"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_news",
            "description": "Get top news headlines for a category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "News topic/category"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_powershell_command",
            "description": "Execute a PowerShell command on the Windows system and return the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "PowerShell command to run"}
                },
                "required": ["command"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a registered tool by name with arguments.
    
    :param tool_name: Registered tool function name.
    :param arguments: Dictionary of arguments.
    :return: Tool execution result dictionary.
    """
    if tool_name not in TOOL_REGISTRY:
        return {"success": False, "error": f"Tool '{tool_name}' is not recognized."}

    func = TOOL_REGISTRY[tool_name]
    try:
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        return func(**arguments)
    except Exception as e:
        return {"success": False, "error": f"Error executing '{tool_name}': {str(e)}"}
