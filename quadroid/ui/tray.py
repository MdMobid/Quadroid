"""
Quadroid System Tray — Minimize to tray, quick actions, and mini-mode toggle.
"""
import threading
from typing import Callable, Optional

try:
    from pystray import Icon, MenuItem, Menu
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


class SystemTray:
    """System tray integration for Quadroid — minimize to tray with quick actions."""

    def __init__(
        self,
        on_show_window: Optional[Callable] = None,
        on_toggle_mini: Optional[Callable] = None,
        on_screenshot: Optional[Callable] = None,
        on_mute_toggle: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
        assistant_name: str = "Quadroid"
    ):
        self.on_show_window = on_show_window
        self.on_toggle_mini = on_toggle_mini
        self.on_screenshot = on_screenshot
        self.on_mute_toggle = on_mute_toggle
        self.on_quit = on_quit
        self.assistant_name = assistant_name
        self.icon: Optional[Icon] = None

    def _create_icon_image(self, color: str = "#00d4ff") -> "Image.Image":
        """Generate a simple colored circle tray icon."""
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Outer glow ring
        draw.ellipse([4, 4, size - 4, size - 4], fill=color, outline=color)

        # Inner dark circle
        draw.ellipse([12, 12, size - 12, size - 12], fill="#0a0e1a")

        # Center dot
        draw.ellipse([24, 24, size - 24, size - 24], fill=color)

        return img

    def start(self):
        """Start the system tray icon in a background thread."""
        if not TRAY_AVAILABLE:
            return

        menu = Menu(
            MenuItem(f"Show {self.assistant_name}", self._on_show, default=True),
            MenuItem("Mini Mode", self._on_mini),
            Menu.SEPARATOR,
            MenuItem("📸 Screenshot", self._on_screenshot),
            MenuItem("🔇 Mute/Unmute", self._on_mute),
            Menu.SEPARATOR,
            MenuItem(f"Quit {self.assistant_name}", self._on_quit_click),
        )

        self.icon = Icon(
            name=self.assistant_name,
            icon=self._create_icon_image(),
            title=f"{self.assistant_name} — AI Desktop Assistant",
            menu=menu
        )

        thread = threading.Thread(target=self.icon.run, daemon=True)
        thread.start()

    def stop(self):
        """Stop the tray icon."""
        if self.icon:
            self.icon.stop()

    def update_status(self, online: bool = True):
        """Update tray icon color based on status."""
        if self.icon:
            color = "#10b981" if online else "#ef4444"
            self.icon.icon = self._create_icon_image(color)

    def _on_show(self, icon=None, item=None):
        if self.on_show_window:
            self.on_show_window()

    def _on_mini(self, icon=None, item=None):
        if self.on_toggle_mini:
            self.on_toggle_mini()

    def _on_screenshot(self, icon=None, item=None):
        if self.on_screenshot:
            self.on_screenshot()

    def _on_mute(self, icon=None, item=None):
        if self.on_mute_toggle:
            self.on_mute_toggle()

    def _on_quit_click(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        if self.on_quit:
            self.on_quit()
