import os
import sys
import math
import time
import threading
import tkinter as tk
from typing import Optional, Dict, Any
from datetime import datetime

from quadroid.config import Config
from quadroid.agent import Agent
from quadroid.audio.speech import speak
from quadroid.audio.listener import listen_and_transcribe
from quadroid.audio.wakeword import WakeWordListener
from quadroid.audio.player import play_sound_async
from quadroid.tools.system import get_battery_status, get_system_stats

# Try CustomTkinter for modern styling
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
except ImportError:
    CTK_AVAILABLE = False


# Theme Palette (Stitch Futuristic HUD)
HUD_BG = "#0b0f19"             # Deep slate glass base
CARD_BG = "#131926"            # Surface container
CARD_BORDER = "#1e293b"        # Card outline
CYAN_ACCENT = "#00f2fe"        # Primary neon cyan
CYAN_HOVER = "#00c8d4"         # Hover cyan
CYAN_GLOW = "#083344"          # Inset cyan glow
EMERALD_ACCENT = "#10b981"     # Secondary emerald
EMERALD_GLOW = "#064e3b"       # Emerald glow
PURPLE_ACCENT = "#7c3aed"      # Tertiary purple
TEXT_PRIMARY = "#f1f5f9"       # Main text
TEXT_MUTED = "#94a3b8"         # Muted telemetry
TEXT_CYAN = "#38bdf8"          # Action chip text


class QuadroidApp(ctk.CTk if CTK_AVAILABLE else tk.Tk):
    """Futuristic High-Tech HUD Desktop Application for Quadroid AI Assistant."""

    def __init__(self):
        super().__init__()

        self.title(f"{Config.ASSISTANT_NAME.upper()} // AI COMMAND HUD")
        self.geometry("540x740")
        self.minsize(480, 640)
        self.configure(fg_color=HUD_BG if CTK_AVAILABLE else "#0b0f19")

        # Assistant Agent
        self.agent = Agent(on_action_callback=self._on_tool_action)

        # State flags
        self.is_listening = False
        self.is_processing = False
        self.anim_phase = 0.0

        # Build UI layout
        self._create_telemetry_header()
        self._create_visualizer_orb()
        self._create_chat_feed()
        self._create_quick_action_pills()
        self._create_control_deck()

        # Welcome message
        self._append_message(
            Config.ASSISTANT_NAME.upper(),
            f"Neural Link Online. Systems operational. Say 'Hey {Config.ASSISTANT_NAME}' or trigger a command.",
            is_user=False
        )

        # Start Telemetry update loop & Orb Animation loop
        self._start_telemetry_loop()
        self._animate_orb()

        # Initialize Wake-Word listener
        if Config.WAKE_WORD_ENABLED:
            self.wakeword_listener = WakeWordListener(on_wake_detected=self._on_wake_word_triggered)
            self.wakeword_listener.start()
        else:
            self.wakeword_listener = None

    def _create_telemetry_header(self):
        """High-Tech Telemetry Gauge Bar."""
        header_frame = ctk.CTkFrame(self, corner_radius=8, fg_color=CARD_BG, border_width=1, border_color=CARD_BORDER)
        header_frame.pack(fill="x", padx=14, pady=(12, 6))

        # Brand / Title
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=12, pady=8)

        logo_lbl = ctk.CTkLabel(
            title_box, 
            text=f"⚡ {Config.ASSISTANT_NAME.upper()}", 
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=CYAN_ACCENT
        )
        logo_lbl.pack(side="left")

        ver_lbl = ctk.CTkLabel(
            title_box,
            text=" v2.0",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=TEXT_MUTED
        )
        ver_lbl.pack(side="left", padx=(4, 0))

        # Telemetry stats on right
        stats_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        stats_box.pack(side="right", padx=12, pady=8)

        # CPU / RAM stats
        self.cpu_lbl = ctk.CTkLabel(
            stats_box,
            text="CPU: 0%",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=TEXT_MUTED
        )
        self.cpu_lbl.pack(side="left", padx=6)

        self.ram_lbl = ctk.CTkLabel(
            stats_box,
            text="RAM: 0%",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=TEXT_MUTED
        )
        self.ram_lbl.pack(side="left", padx=6)

        # Mode Badge
        is_off = Config.is_offline()
        mode_text = "🔒 OFFLINE" if is_off else "🌐 CLOUD"
        mode_color = EMERALD_ACCENT if is_off else CYAN_ACCENT

        self.mode_badge = ctk.CTkLabel(
            stats_box,
            text=mode_text,
            font=ctk.CTkFont(family="JetBrains Mono", size=10, weight="bold"),
            text_color=mode_color,
            fg_color="#0a192f" if is_off else "#082f49",
            corner_radius=4,
            padx=6,
            pady=2
        )
        self.mode_badge.pack(side="left", padx=(6, 0))

    def _create_visualizer_orb(self):
        """Holographic AI Core / Pulse Canvas Visualizer."""
        self.orb_container = ctk.CTkFrame(self, height=44, fg_color="transparent")
        self.orb_container.pack(fill="x", padx=14, pady=(2, 4))

        self.orb_canvas = tk.Canvas(
            self.orb_container, 
            height=40, 
            bg=HUD_BG, 
            highlightthickness=0
        )
        self.orb_canvas.pack(fill="x", expand=True)

    def _animate_orb(self):
        """Dynamic Soundwave / Hologram Orb Animation."""
        self.orb_canvas.delete("all")
        width = self.orb_canvas.winfo_width()
        height = 40
        if width > 10:
            center_x = width / 2
            center_y = height / 2

            # Waveform bars
            num_bars = 28
            bar_spacing = 7
            start_x = center_x - (num_bars * bar_spacing) / 2

            color = CYAN_ACCENT
            multiplier = 1.0
            if self.is_listening:
                color = "#f43f5e"  # Neon Rose when listening
                multiplier = 2.4
            elif self.is_processing:
                color = "#a855f7"  # Neon Purple when thinking
                multiplier = 1.8

            for i in range(num_bars):
                dist_from_center = abs(i - num_bars / 2) / (num_bars / 2)
                base_h = math.sin(self.anim_phase + i * 0.4) * (12 * multiplier) * (1 - dist_from_center * 0.6)
                h = max(3, abs(base_h))
                x = start_x + i * bar_spacing
                self.orb_canvas.create_line(
                    x, center_y - h, x, center_y + h,
                    fill=color,
                    width=2,
                    capstyle=tk.ROUND
                )

        self.anim_phase += 0.15
        self.after(40, self._animate_orb)

    def _create_chat_feed(self):
        """Scrollable Holographic Chat & Action Stream."""
        self.chat_frame = ctk.CTkScrollableFrame(
            self, 
            corner_radius=10, 
            fg_color=CARD_BG,
            border_width=1,
            border_color=CARD_BORDER
        )
        self.chat_frame.pack(fill="both", expand=True, padx=14, pady=4)

    def _create_quick_action_pills(self):
        """Cyber Command Pills for Instant Execution."""
        pills_frame = ctk.CTkScrollableFrame(
            self, 
            height=36, 
            orientation="horizontal", 
            fg_color="transparent"
        )
        pills_frame.pack(fill="x", padx=12, pady=(4, 2))

        pills = [
            ("📸 Screenshot", "Take a screenshot"),
            ("🔊 Mute Audio", "Mute system audio"),
            ("🔋 Battery", "Check my battery percentage"),
            ("⚡ System Health", "Get system stats"),
            ("📝 Take Note", "Save a note 'Follow up task' with 'Review project specs'"),
            ("📁 Find Files", "Search for files on my computer"),
            ("⛅ Weather", "What is the weather today?"),
        ]

        for label, cmd in pills:
            btn = ctk.CTkButton(
                pills_frame,
                text=label,
                font=ctk.CTkFont(family="Inter", size=11),
                fg_color="#1e293b",
                hover_color="#334155",
                text_color=TEXT_PRIMARY,
                border_width=1,
                border_color="#334155",
                height=26,
                corner_radius=13,
                command=lambda c=cmd: self._process_user_query(c)
            )
            btn.pack(side="left", padx=3)

    def _create_control_deck(self):
        """Futuristic Input Control Deck."""
        deck_frame = ctk.CTkFrame(self, fg_color="transparent")
        deck_frame.pack(fill="x", padx=14, pady=(4, 12))

        # Glowing Neon Mic button
        self.mic_btn = ctk.CTkButton(
            deck_frame, 
            text="🎙️", 
            width=44, 
            height=44, 
            corner_radius=22,
            fg_color=CYAN_ACCENT,
            hover_color=CYAN_HOVER,
            text_color="#000000",
            font=ctk.CTkFont(size=18),
            command=self._toggle_voice_input
        )
        self.mic_btn.pack(side="left", padx=(0, 8))

        # Rounded Cyber Text Entry
        self.text_entry = ctk.CTkEntry(
            deck_frame, 
            placeholder_text=f"Enter command or directive (or say 'Hey {Config.ASSISTANT_NAME}')...",
            placeholder_text_color="#64748b",
            font=ctk.CTkFont(family="Inter", size=12),
            height=44,
            corner_radius=22,
            fg_color="#182234",
            border_color="#22334e",
            border_width=1,
            text_color="#ffffff"
        )
        self.text_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.text_entry.bind("<Return>", lambda e: self._on_send_clicked())

        # Send action button
        self.send_btn = ctk.CTkButton(
            deck_frame, 
            text="➔", 
            width=44, 
            height=44, 
            corner_radius=22,
            fg_color="#1e293b",
            hover_color="#334155",
            border_width=1,
            border_color=CYAN_ACCENT,
            font=ctk.CTkFont(family="JetBrains Mono", size=16, weight="bold"),
            text_color=CYAN_ACCENT,
            command=self._on_send_clicked
        )
        self.send_btn.pack(side="right")

    def _start_telemetry_loop(self):
        """Update CPU, RAM, and Battery in Background Loop."""
        def _update():
            stats = get_system_stats()
            bat = get_battery_status()
            if stats.get("success"):
                cpu = stats.get("cpu_usage_percent", 0)
                ram = stats.get("ram_percent", 0)
                self.cpu_lbl.configure(text=f"CPU: {cpu}%")
                self.ram_lbl.configure(text=f"RAM: {ram}%")
            self.after(3000, self._start_telemetry_loop)
        threading.Thread(target=_update, daemon=True).start()

    def _append_message(self, sender: str, text: str, is_user: bool = False):
        """Append a cyber styled message card."""
        def _insert():
            card = ctk.CTkFrame(
                self.chat_frame,
                corner_radius=8,
                fg_color="#1e293b" if is_user else "#0f172a",
                border_width=1,
                border_color=CYAN_ACCENT if is_user else "#1e293b"
            )
            card.pack(
                anchor="e" if is_user else "w",
                padx=8,
                pady=4,
                fill="none"
            )

            header_lbl = ctk.CTkLabel(
                card,
                text=f"{'👤 ' + sender if is_user else '🤖 ' + sender}",
                font=ctk.CTkFont(family="JetBrains Mono", size=10, weight="bold"),
                text_color=CYAN_ACCENT if is_user else EMERALD_ACCENT
            )
            header_lbl.pack(anchor="w", padx=12, pady=(8, 0))

            content_lbl = ctk.CTkLabel(
                card,
                text=text,
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=TEXT_PRIMARY,
                wraplength=380,
                justify="left"
            )
            content_lbl.pack(padx=12, pady=(2, 10))

        self.after(0, _insert)

    def _append_action_chip(self, tool_name: str, args: dict):
        """Display glowing Cyber Action Chip."""
        def _insert():
            display_args = ", ".join(f"{k}={v}" for k, v in args.items()) if args else ""
            action_text = f"⚙️ EXECUTING: {tool_name}({display_args})"
            
            chip = ctk.CTkLabel(
                self.chat_frame,
                text=action_text,
                font=ctk.CTkFont(family="JetBrains Mono", size=10),
                text_color=TEXT_CYAN,
                fg_color="#082f49",
                corner_radius=4,
                padx=10,
                pady=4
            )
            chip.pack(anchor="w", padx=12, pady=2)
        self.after(0, _insert)

    def _on_tool_action(self, tool_name: str, args: dict):
        self._append_action_chip(tool_name, args)

    def _on_send_clicked(self):
        text = self.text_entry.get().strip()
        if not text or self.is_processing:
            return
        self.text_entry.delete(0, "end")
        self._process_user_query(text)

    def _process_user_query(self, user_query: str):
        self.is_processing = True
        self._append_message("OPERATOR", user_query, is_user=True)

        def _worker():
            try:
                play_sound_async("interface.mp3")
                result = self.agent.process_input(user_query)
                reply = result.get("response", "Task completed.")
                
                self._append_message(Config.ASSISTANT_NAME.upper(), reply, is_user=False)
                
                if Config.ENABLE_VOICE_FEEDBACK:
                    speak(reply, async_mode=True)

            except Exception as e:
                self._append_message(Config.ASSISTANT_NAME.upper(), f"SYSTEM ALERT: {str(e)}", is_user=False)
            finally:
                self.is_processing = False

        threading.Thread(target=_worker, daemon=True).start()

    def _toggle_voice_input(self):
        """Trigger microphone speech recognition."""
        if self.is_listening or self.is_processing:
            return

        def _listen_worker():
            self.is_listening = True
            self.mic_btn.configure(fg_color="#f43f5e")
            
            play_sound_async("wake-up.mp3")
            transcript = listen_and_transcribe(timeout=5.0, phrase_time_limit=10.0)

            self.mic_btn.configure(fg_color=CYAN_ACCENT)
            self.is_listening = False

            if transcript:
                self._process_user_query(transcript)

        threading.Thread(target=_listen_worker, daemon=True).start()

    def _on_wake_word_triggered(self):
        """Invoked when user says 'Hey Quadroid'."""
        self.after(0, self._bring_to_front)
        self._toggle_voice_input()

    def _bring_to_front(self):
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after_idle(self.attributes, "-topmost", False)


def launch_gui():
    """Launch the Quadroid Desktop Application."""
    app = QuadroidApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
