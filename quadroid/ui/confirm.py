"""
Quadroid Confirmation Dialog — Windows-style popup for dangerous actions.

Provides a thread-safe modal confirmation dialog that works from
background threads (agent worker threads) by dispatching to the
Tkinter main loop.
"""
import threading
from typing import Optional

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

# Global reference to the main GUI app window (set by gui.py on launch)
_app_root: Optional[object] = None
_confirmation_lock = threading.Lock()


def set_app_root(root):
    """Register the main GUI root window for dialog positioning."""
    global _app_root
    _app_root = root


def request_confirmation(
    title: str,
    message: str,
    action_type: str = "warning"
) -> bool:
    """
    Show a modal confirmation popup and block until the user responds.
    Thread-safe: can be called from any background thread.

    :param title: Popup title (e.g., 'Delete File')
    :param message: Description of the action (e.g., 'Delete C:\\report.pdf?')
    :param action_type: 'warning' (amber), 'danger' (red), or 'info' (cyan)
    :returns: True if user approved, False if denied
    """
    result_event = threading.Event()
    user_choice = {"approved": False}

    def _show_dialog():
        with _confirmation_lock:
            dialog = _ConfirmationDialog(
                parent=_app_root,
                title=title,
                message=message,
                action_type=action_type,
                on_result=lambda approved: _on_result(approved, result_event, user_choice)
            )
            dialog.focus_force()

    def _on_result(approved, event, choice):
        choice["approved"] = approved
        event.set()

    # Dispatch dialog creation to the main Tkinter thread
    if _app_root is not None:
        _app_root.after(0, _show_dialog)
    else:
        # No GUI — fallback to console confirmation
        print(f"\n⚠️  CONFIRMATION REQUIRED: {title}")
        print(f"   {message}")
        answer = input("   Allow? (y/n): ").strip().lower()
        return answer in ("y", "yes")

    # Block calling thread until user clicks Allow/Deny
    result_event.wait(timeout=120)  # 2-minute timeout
    return user_choice["approved"]


class _ConfirmationDialog(ctk.CTkToplevel if CTK_AVAILABLE else object):
    """Dark-themed confirmation popup matching Quadroid's HUD aesthetic."""

    # Color palette
    COLORS = {
        "warning": {"icon": "⚠️", "accent": "#f59e0b", "bg_accent": "#451a03", "btn": "#f59e0b", "btn_hover": "#d97706"},
        "danger":  {"icon": "🛑", "accent": "#ef4444", "bg_accent": "#450a0a", "btn": "#ef4444", "btn_hover": "#dc2626"},
        "info":    {"icon": "ℹ️", "accent": "#00d4ff", "bg_accent": "#082f49", "btn": "#00d4ff", "btn_hover": "#0ea5e9"},
    }

    def __init__(self, parent, title, message, action_type, on_result):
        super().__init__(parent)

        self.on_result = on_result
        colors = self.COLORS.get(action_type, self.COLORS["warning"])

        # Window setup
        self.title(f"Quadroid — {title}")
        self.geometry("440x260")
        self.resizable(False, False)
        self.configure(fg_color="#0a0e1a")
        self.attributes("-topmost", True)
        self.grab_set()  # Make modal

        # Center on screen or parent
        self.update_idletasks()
        if parent:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 220
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 130
        else:
            x = (self.winfo_screenwidth() // 2) - 220
            y = (self.winfo_screenheight() // 2) - 130
        self.geometry(f"+{x}+{y}")

        # ── Header with icon ──
        header_frame = ctk.CTkFrame(self, fg_color=colors["bg_accent"], corner_radius=10)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        icon_label = ctk.CTkLabel(
            header_frame,
            text=f"{colors['icon']}  {title}",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=colors["accent"]
        )
        icon_label.pack(padx=16, pady=12)

        # ── Message body ──
        msg_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(family="Inter", size=13),
            text_color="#e2e8f0",
            wraplength=390,
            justify="center"
        )
        msg_label.pack(padx=20, pady=(10, 20))

        # ── Action buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Deny button (left)
        deny_btn = ctk.CTkButton(
            btn_frame,
            text="✕  Deny",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            text_color="#f87171",
            border_width=1,
            border_color="#334155",
            height=40,
            corner_radius=10,
            width=180,
            command=self._on_deny
        )
        deny_btn.pack(side="left", expand=True, padx=(0, 8))

        # Allow button (right)
        allow_btn = ctk.CTkButton(
            btn_frame,
            text="✓  Allow",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color=colors["btn"],
            hover_color=colors["btn_hover"],
            text_color="#000000",
            height=40,
            corner_radius=10,
            width=180,
            command=self._on_allow
        )
        allow_btn.pack(side="right", expand=True, padx=(8, 0))

        # Handle window close (X button) as denial
        self.protocol("WM_DELETE_WINDOW", self._on_deny)

    def _on_allow(self):
        self.grab_release()
        self.destroy()
        self.on_result(True)

    def _on_deny(self):
        self.grab_release()
        self.destroy()
        self.on_result(False)
