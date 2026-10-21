"""
Quadroid Agent — High-performance AI coordinator with fast LLM tool calling, zero-latency in-memory context, and offline fallback.
"""
import re
import json
import uuid
from typing import List, Dict, Any, Callable, Optional
from quadroid.config import Config
from quadroid.core.prompts import QUADROID_SYSTEM_PROMPT
from quadroid.core.llm import LLMClient
from quadroid.tools import execute_tool


class Agent:
    """Core Quadroid Agent with Fast LLM Tool Calling and Built-in Offline Fallback Router."""

    def __init__(self, on_action_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        self.llm_client = LLMClient()
        self.on_action_callback = on_action_callback
        self.session_id = str(uuid.uuid4())[:8]
        self.history: List[Dict[str, Any]] = [
            {"role": "system", "content": QUADROID_SYSTEM_PROMPT}
        ]
        self.max_history = 10
        self.memory = None

    def reset_history(self):
        """Reset conversation context."""
        self.history = [{"role": "system", "content": QUADROID_SYSTEM_PROMPT}]

    def _trigger_action(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to invoke a tool with action callback notification."""
        if self.on_action_callback:
            self.on_action_callback(tool_name, args)
        return execute_tool(tool_name, args)

    def _fallback_intent_router(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Rule-based intent parser to ensure essential desktop tasks work accurately
        and instantly even if the local LLM/Ollama is offline or busy.
        """
        clean_low = text.lower().strip()

        # Multi-pass conversational phrase cleaning (strips wake words, polite requests, and trailing fillers)
        cleaning_patterns = [
            r'^(?:hey|ok|hello|hi)\s+(?:max|quadroid)[,:]?\s*',
            r'^(?:max|quadroid)[,:]?\s*',
            r'^(?:can|could|will|would)\s+you\s+(?:please\s+)?(?:help\s+me\s+)?(?:to\s+)?',
            r'^(?:please\s+)?(?:help\s+me\s+)?(?:to\s+)?',
            r'\s+(?:for\s+me|please|now|right\s+now)[.!]?$'
        ]
        
        for p in cleaning_patterns:
            clean_low = re.sub(p, '', clean_low, flags=re.IGNORECASE).strip()

        low = clean_low if clean_low else text.lower().strip()

        # 1. Volume mute/unmute
        if "unmute" in low:
            res = self._trigger_action("mute_system_volume", {"mute": False})
            return {"response": "System audio unmuted.", "actions": [{"tool": "mute_system_volume", "result": res}]}
        if ("mute" in low and "volume" in low) or low == "mute" or "mute audio" in low:
            res = self._trigger_action("mute_system_volume", {"mute": True})
            return {"response": "System audio muted.", "actions": [{"tool": "mute_system_volume", "result": res}]}

        # 2. Volume level
        vol_match = re.search(r'(?:volume\s+(?:to\s+)?|set\s+volume\s+(?:to\s+)?)(\d{1,3})%?', low)
        if vol_match:
            val = int(vol_match.group(1))
            res = self._trigger_action("set_system_volume", {"level": val})
            return {"response": f"Master volume set to {val}%.", "actions": [{"tool": "set_system_volume", "result": res}]}

        # 3. Brightness level
        bright_match = re.search(r'(?:brightness\s+(?:to\s+)?|set\s+brightness\s+(?:to\s+)?)(\d{1,3})%?', low)
        if bright_match:
            val = int(bright_match.group(1))
            res = self._trigger_action("set_screen_brightness", {"level": val})
            return {"response": f"Display brightness set to {val}%.", "actions": [{"tool": "set_screen_brightness", "result": res}]}

        # 4. Open folders vs Screenshot capture
        if "open" in low and ("screenshot folder" in low or "screenshots folder" in low):
            res = self._trigger_action("open_path_in_explorer", {"path": str(Config.SCREENSHOTS_DIR)})
            return {"response": "Opened screenshots folder.", "actions": [{"tool": "open_path_in_explorer", "result": res}]}
        if "open" in low and ("download" in low and "folder" in low):
            import pathlib
            downloads = str(pathlib.Path.home() / "Downloads")
            res = self._trigger_action("open_path_in_explorer", {"path": downloads})
            return {"response": "Opened Downloads folder.", "actions": [{"tool": "open_path_in_explorer", "result": res}]}
        if "screenshot" in low or "screen capture" in low:
            res = self._trigger_action("take_screenshot", {})
            msg = res.get("message", "Screenshot captured.")
            return {"response": f"Captured screenshot! {msg}", "actions": [{"tool": "take_screenshot", "result": res}]}

        # 5. Battery & Power
        if "battery" in low or "power" in low:
            res = self._trigger_action("get_battery_status", {})
            msg = res.get("message", "Battery status retrieved.")
            return {"response": msg, "actions": [{"tool": "get_battery_status", "result": res}]}

        # 6. System stats / Health
        if "system stats" in low or "system health" in low or "cpu" in low or "ram" in low or "specs" in low:
            res = self._trigger_action("get_system_stats", {})
            msg = res.get("message", "System resources active.")
            return {"response": msg, "actions": [{"tool": "get_system_stats", "result": res}]}

        # 7. Lock workstation
        if "lock screen" in low or "lock pc" in low or "lock workstation" in low or low == "lock":
            res = self._trigger_action("lock_workstation", {})
            return {"response": "Locking workstation now.", "actions": [{"tool": "lock_workstation", "result": res}]}

        # 8. Web Search / Specific Site Search (e.g. "open chrome and search for youtube", "search github for fastapi")
        search_match = re.search(r'(?:open\s+(?:google\s+)?chrome\s+and\s+)?search\s+(?:(google|github|youtube)\s+for\s+|for\s+)?(?:on\s+(google|github|youtube)\s+)?(.+)', low)
        if search_match:
            engine = search_match.group(1) or search_match.group(2) or "google"
            query = search_match.group(3).strip()
            
            if " on youtube" in query:
                engine = "youtube"
                query = query.replace(" on youtube", "").strip()
            elif " on github" in query:
                engine = "github"
                query = query.replace(" on github", "").strip()
            elif " on google" in query:
                query = query.replace(" on google", "").strip()

            if query:
                res = self._trigger_action("web_search", {"query": query, "engine": engine})
                return {"response": f"Searching for '{query}' on {engine.title()}.", "actions": [{"tool": "web_search", "result": res}]}

        # 9. Direct Website URLs (e.g. "open youtube", "open github")
        quick_sites = {
            "youtube": "https://youtube.com",
            "github": "https://github.com",
            "google": "https://google.com",
            "reddit": "https://reddit.com",
            "twitter": "https://x.com",
            "netflix": "https://netflix.com",
            "chatgpt": "https://chatgpt.com",
            "linkedin": "https://linkedin.com"
        }
        site_match = re.match(r'^(?:open|go\s+to|launch)\s+([a-zA-Z0-9_-]+)(?:\.com|\.org|\.io)?$', low)
        if site_match:
            site_key = site_match.group(1).lower()
            if site_key in quick_sites:
                target_url = quick_sites[site_key]
                res = self._trigger_action("open_url", {"url": target_url})
                return {"response": f"Opening {site_key.title()} in browser.", "actions": [{"tool": "open_url", "result": res}]}

        # 10. Email / Gmail compose
        if "email" in low or "gmail" in low or "mail" in low:
            if "write" in low or "send" in low or "compose" in low or "open" in low:
                to_match = re.search(r'(?:to)\s+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', text)
                to_addr = to_match.group(1) if to_match else ""
                su_match = re.search(r'(?:about|subject)\s+([^,.]+)', text, re.IGNORECASE)
                subject = su_match.group(1).strip() if su_match else ""
                
                res = self._trigger_action("compose_email", {"to": to_addr, "subject": subject, "body": ""})
                return {"response": f"Opened Gmail draft{' for ' + to_addr if to_addr else ''}.", "actions": [{"tool": "compose_email", "result": res}]}

        # 11. Weather
        if "weather" in low:
            city_match = re.search(r'weather\s+(?:in|for|at)?\s*([a-zA-Z\s]+)', low)
            city = city_match.group(1).strip() if city_match else ""
            res = self._trigger_action("get_weather", {"city": city})
            summary = res.get("summary", "Could not retrieve weather.")
            return {"response": summary, "actions": [{"tool": "get_weather", "result": res}]}

        # 12. Open / Close Application
        open_match = re.match(r'^(?:open|launch|start)\s+(.+)$', low)
        if open_match:
            target_app = open_match.group(1).strip()
            res = self._trigger_action("open_application", {"app_name": target_app})
            return {"response": f"Opening {target_app}.", "actions": [{"tool": "open_application", "result": res}]}

        close_match = re.match(r'^(?:close|exit|terminate|kill)\s+(.+)$', low)
        if close_match:
            target_app = close_match.group(1).strip()
            res = self._trigger_action("close_application", {"app_name": target_app})
            msg = res.get("message", f"Closed {target_app}.")
            return {"response": msg, "actions": [{"tool": "close_application", "result": res}]}

        # 13. File search
        if "search for" in low or "find file" in low or "find" in low:
            query = low.replace("search for", "").replace("find files", "").replace("find file", "").replace("find", "").strip()
            if query:
                res = self._trigger_action("search_files", {"query": query})
                files = res.get("files", [])
                if files:
                    file_list = "\n".join(files[:3])
                    return {"response": f"Found {len(files)} matches:\n{file_list}", "actions": [{"tool": "search_files", "result": res}]}
                else:
                    return {"response": f"No files matching '{query}' found.", "actions": [{"tool": "search_files", "result": res}]}

        return None

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user request via fast LLM tool calling with intelligent local fallback.
        """
        user_input = user_input.strip()
        if not user_input:
            return {"response": "I didn't catch that. Please type or speak again.", "actions": []}

        # Add user message to history sliding window
        self.history.append({"role": "user", "content": user_input})
        if len(self.history) > self.max_history:
            self.history = [self.history[0]] + self.history[-(self.max_history - 1):]

        actions_taken = []

        # 1. Fast LLM Completion
        try:
            response = self.llm_client.chat_completion(messages=self.history)
            response_msg = response.choices[0].message

            if response_msg.tool_calls:
                self.history.append(response_msg.to_dict() if hasattr(response_msg, "to_dict") else {
                    "role": "assistant",
                    "content": response_msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in response_msg.tool_calls
                    ]
                })

                for tool_call in response_msg.tool_calls:
                    func_name = tool_call.function.name
                    func_args_raw = tool_call.function.arguments
                    try:
                        func_args = json.loads(func_args_raw) if isinstance(func_args_raw, str) else func_args_raw
                    except Exception:
                        func_args = {}

                    result = self._trigger_action(func_name, func_args)
                    actions_taken.append({"tool": func_name, "args": func_args, "result": result})

                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": json.dumps(result)
                    })

                final_response = self.llm_client.chat_completion(messages=self.history)
                final_text = final_response.choices[0].message.content or "Done."
                self.history.append({"role": "assistant", "content": final_text})

                return {"response": final_text, "actions": actions_taken, "success": True}

            else:
                reply_text = response_msg.content or "Acknowledged."
                self.history.append({"role": "assistant", "content": reply_text})
                return {"response": reply_text, "actions": [], "success": True}

        except Exception:
            # 2. Instant local rule fallback
            fallback_res = self._fallback_intent_router(user_input)
            if fallback_res:
                self.history.append({"role": "assistant", "content": fallback_res["response"]})
                return {
                    "response": fallback_res["response"],
                    "actions": fallback_res.get("actions", []),
                    "success": True
                }

            msg = f"Acknowledged '{user_input}'. To enable complex generative reasoning, please start Ollama or configure an API key in your .env file."
            self.history.append({"role": "assistant", "content": msg})
            return {"response": msg, "actions": [], "success": True}
