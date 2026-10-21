"""
Quadroid Mini-Mode — Floating transparent orb overlay for minimal desktop presence.
A tiny draggable window with animated waveform and mic button.
"""
import math
import tkinter as tk
from typing import Optional, Callable

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


class MiniModeWindow(ctk.CTkToplevel if CTK_AVAILABLE else tk.Toplevel):
    """Floating 140x140px transparent orb — draggable, always-on-top, minimal HUD."""

    def __init__(self, parent, on_expand: Optional[Callable] = None, on_mic: Optional[Callable] = None):
        super().__init__(parent)

        self.on_expand = on_expand
        self.on_mic = on_mic
        self.anim_phase = 0.0
        self.is_listening = False
        self.is_processing = False

        # Window setup — frameless, transparent, always-on-top
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#0a0e1a" if CTK_AVAILABLE else None)
        if not CTK_AVAILABLE:
            self.configure(bg="#0a0e1a")

        # Position bottom-right of screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"140x140+{screen_w - 180}+{screen_h - 220}")

        # Draggable state
        self._drag_x = 0
        self._drag_y = 0

        # Build mini orb UI
        self._create_orb()

        # Start animation
        self._animate()

    def _create_orb(self):
        """Build the floating orb canvas with mic button."""
        # Orb canvas
        self.canvas = tk.Canvas(
            self,
            width=140,
            height=100,
            bg="#0a0e1a",
            highlightthickness=0
        )
        self.canvas.pack(fill="x", pady=(0, 0))

        # Make canvas draggable
        self.canvas.bind("<Button-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._do_drag)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

        # Mic button
        btn_frame = tk.Frame(self, bg="#0a0e1a")
        btn_frame.pack(fill="x")

        if CTK_AVAILABLE:
            self.mic_btn = ctk.CTkButton(
                btn_frame,
                text="🎙️",
                width=50,
                height=32,
                corner_radius=16,
                fg_color="#00d4ff",
                hover_color="#0ea5e9",
                text_color="#000000",
                font=ctk.CTkFont(size=14),
                command=self._on_mic_click
            )
            self.mic_btn.pack(side="left", padx=8)

            expand_btn = ctk.CTkButton(
                btn_frame,
                text="⬆",
                width=50,
                height=32,
                corner_radius=16,
                fg_color="#1e293b",
                hover_color="#334155",
                text_color="#94a3b8",
                font=ctk.CTkFont(size=14),
                command=self._on_expand_click
            )
            expand_btn.pack(side="right", padx=8)

    def _animate(self):
        """Animate the mini waveform."""
        self.canvas.delete("all")
        w = 140
        h = 100
        cx = w / 2
        cy = h / 2

        # Draw circular glow backdrop
        color = "#00d4ff"
        if self.is_listening:
            color = "#f43f5e"
        elif self.is_processing:
            color = "#a855f7"

        # Subtle glow ring
        self.canvas.create_oval(
            20, 10, w - 20, h - 10,
            outline=color,
            width=1,
            dash=(3, 3)
        )

        # Waveform bars
        num_bars = 16
        spacing = 5
        start_x = cx - (num_bars * spacing) / 2
        multiplier = 2.2 if self.is_listening else (1.6 if self.is_processing else 0.8)

        for i in range(num_bars):
            dist = abs(i - num_bars / 2) / (num_bars / 2)
            base_h = math.sin(self.anim_phase + i * 0.5) * (16 * multiplier) * (1 - dist * 0.5)
            bar_h = max(2, abs(base_h))
            x = start_x + i * spacing

            self.canvas.create_line(
                x, cy - bar_h, x, cy + bar_h,
                fill=color,
                width=2,
                capstyle=tk.ROUND
            )

        self.anim_phase += 0.12
        self.after(50, self._animate)

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _on_double_click(self, event):
        """Double-click on orb expands to full GUI."""
        if self.on_expand:
            self.on_expand()

    def _on_mic_click(self):
        if self.on_mic:
            self.on_mic()

    def _on_expand_click(self):
        if self.on_expand:
            self.on_expand()

    def set_state(self, listening: bool = False, processing: bool = False):
        """Update visual state."""
        self.is_listening = listening
        self.is_processing = processing
        if CTK_AVAILABLE and hasattr(self, 'mic_btn'):
            color = "#f43f5e" if listening else "#00d4ff"
            self.mic_btn.configure(fg_color=color)
