"""
Quadroid v3.0 — Professional HUD Command Center
Complete rewrite with sidebar navigation, real-time FFT waveform, markdown chat,
typing indicators, status bar, system tray, and mini-mode.
"""
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
from quadroid.ui.confirm import set_app_root
from quadroid.ui.tray import SystemTray
from quadroid.ui.mini_mode import MiniModeWindow

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
except ImportError:
    CTK_AVAILABLE = False

# ── Professional Color Palette ──
BG_DEEP        = "#0a0e1a"     # Deepest background
BG_SURFACE     = "#111827"     # Card / panel surfaces
BG_SIDEBAR     = "#0d1321"     # Sidebar background
ACCENT_CYAN    = "#00d4ff"     # Primary electric cyan
ACCENT_PURPLE  = "#8b5cf6"     # Secondary vivid purple
ACCENT_EMERALD = "#10b981"     # Success / online
ACCENT_RED     = "#ef4444"     # Danger / listening
ACCENT_AMBER   = "#f59e0b"     # Warning
TEXT_PRIMARY   = "#f1f5f9"     # Primary text
TEXT_SECONDARY = "#94a3b8"     # Secondary / muted
TEXT_DIM       = "#64748b"     # Dimmed labels
BORDER_GLOW    = "#1e3a5f"     # Subtle blue border
SIDEBAR_HOVER  = "#1a2332"     # Sidebar item hover
SIDEBAR_ACTIVE = "#162032"     # Sidebar item active


class QuadroidApp(ctk.CTk if CTK_AVAILABLE else tk.Tk):
    """Quadroid v3.0 — Professional AI Command Center with sidebar navigation."""

    def __init__(self):
        super().__init__()

        # Register this window for confirmation popups
        set_app_root(self)

        self.title(f"{Config.ASSISTANT_NAME.upper()} // AI COMMAND CENTER")
        self.geometry("780x680")
        self.minsize(640, 560)
        self.configure(fg_color=BG_DEEP if CTK_AVAILABLE else BG_DEEP)

        # Assistant Agent
        self.agent = Agent(on_action_callback=self._on_tool_action)

        # State
        self.is_listening = False
        self.is_processing = False
        self.anim_phase = 0.0
        self.current_view = "chat"
        self.start_time = time.time()
        self.mini_window: Optional[MiniModeWindow] = None

        # Build layout
        self._create_main_layout()

        # Welcome
        self._append_message(
            Config.ASSISTANT_NAME.upper(),
            f"Systems online. Ready to assist. Say 'Hey {Config.ASSISTANT_NAME}' or type a command.",
            is_user=False
        )

        # Start background loops
        self._start_telemetry_loop()
        self._animate_waveform()
        self._update_status_bar()

        # Wake-word listener
        if Config.WAKE_WORD_ENABLED:
            self.wakeword_listener = WakeWordListener(on_wake_detected=self._on_wake_word_triggered)
            self.wakeword_listener.start()
        else:
            self.wakeword_listener = None

        # System tray
        self.tray = SystemTray(
            on_show_window=lambda: self.after(0, self._bring_to_front),
            on_toggle_mini=lambda: self.after(0, self._toggle_mini_mode),
            on_screenshot=lambda: self.after(0, lambda: self._process_user_query("take a screenshot")),
            on_mute_toggle=lambda: self.after(0, lambda: self._process_user_query("mute system audio")),
            on_quit=lambda: self.after(0, self._on_quit),
            assistant_name=Config.ASSISTANT_NAME
        )
        self.tray.start()

        # Handle window close → minimize to tray
        self.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)

    # ═══════════════════════════════════════
    # LAYOUT
    # ═══════════════════════════════════════

    def _create_main_layout(self):
        """Create the full app layout: header → [sidebar | content] → status bar."""
        # ── Top Header Bar ──
        self._create_header()

        # ── Body: Sidebar + Content ──
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.body_frame.grid_columnconfigure(1, weight=1)
        self.body_frame.grid_rowconfigure(0, weight=1)

        self._create_sidebar()
        self._create_content_area()

        # ── Bottom Status Bar ──
        self._create_status_bar()

    def _create_header(self):
        """Professional header with logo, telemetry, and mode badge."""
        header = ctk.CTkFrame(self, height=46, corner_radius=0, fg_color=BG_SURFACE,
                              border_width=1, border_color=BORDER_GLOW)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Brand
        brand_frame = ctk.CTkFrame(header, fg_color="transparent")
        brand_frame.pack(side="left", padx=16)

        ctk.CTkLabel(
            brand_frame,
            text=f"◆ {Config.ASSISTANT_NAME.upper()}",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=ACCENT_CYAN
        ).pack(side="left")

        ctk.CTkLabel(
            brand_frame,
            text="  v3.0",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=TEXT_DIM
        ).pack(side="left")

        # Right: Telemetry
        stats_frame = ctk.CTkFrame(header, fg_color="transparent")
        stats_frame.pack(side="right", padx=16)

        self.cpu_lbl = ctk.CTkLabel(
            stats_frame, text="CPU 0%",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=TEXT_SECONDARY
        )
        self.cpu_lbl.pack(side="left", padx=8)

        self.ram_lbl = ctk.CTkLabel(
            stats_frame, text="RAM 0%",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=TEXT_SECONDARY
        )
        self.ram_lbl.pack(side="left", padx=8)

        # Mode badge
        is_off = Config.is_offline()
        mode_text = "🔒 OFFLINE" if is_off else "🌐 ONLINE"
        mode_color = ACCENT_EMERALD if not is_off else ACCENT_AMBER

        self.mode_badge = ctk.CTkLabel(
            stats_frame, text=mode_text,
            font=ctk.CTkFont(family="JetBrains Mono", size=10, weight="bold"),
            text_color=mode_color,
            fg_color=BG_DEEP,
            corner_radius=4, padx=8, pady=2
        )
        self.mode_badge.pack(side="left", padx=(8, 0))

    def _create_sidebar(self):
        """Icon-based vertical sidebar navigation."""
        self.sidebar = ctk.CTkFrame(
            self.body_frame, width=58, corner_radius=0,
            fg_color=BG_SIDEBAR, border_width=1, border_color=BORDER_GLOW
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        nav_items = [
            ("💬", "chat",    "Chat"),
            ("🏠", "home",    "Home"),
            ("🧠", "memory",  "Memory"),
            ("📊", "system",  "System"),
            ("⚙️", "settings","Settings"),
        ]

        self.nav_buttons = {}
        for icon, view_id, tooltip in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=icon,
                width=44, height=44,
                corner_radius=10,
                fg_color=SIDEBAR_ACTIVE if view_id == "chat" else "transparent",
                hover_color=SIDEBAR_HOVER,
                font=ctk.CTkFont(size=18),
                text_color=TEXT_PRIMARY,
                command=lambda v=view_id: self._switch_view(v)
            )
            btn.pack(pady=4, padx=7)
            self.nav_buttons[view_id] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent", height=1).pack(expand=True)

        # Mini-mode toggle at bottom
        ctk.CTkButton(
            self.sidebar,
            text="◉",
            width=44, height=44,
            corner_radius=10,
            fg_color="transparent",
            hover_color=SIDEBAR_HOVER,
            font=ctk.CTkFont(size=16),
            text_color=TEXT_DIM,
            command=self._toggle_mini_mode
        ).pack(pady=(4, 10), padx=7)

    def _create_content_area(self):
        """Content area that switches between views."""
        self.content_frame = ctk.CTkFrame(self.body_frame, fg_color=BG_DEEP, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        # Create all views (but only show current)
        self.views: Dict[str, ctk.CTkFrame] = {}
        self._create_chat_view()
        self._create_home_view()
        self._create_memory_view()
        self._create_system_view()
        self._create_settings_view()

        # Show default view
        self._switch_view("chat")

    def _create_status_bar(self):
        """Bottom status bar with connection, memory, uptime."""
        self.status_bar = ctk.CTkFrame(self, height=28, corner_radius=0,
                                        fg_color=BG_SURFACE, border_width=1, border_color=BORDER_GLOW)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.status_provider = ctk.CTkLabel(
            self.status_bar,
            text=f"⚡ {self.agent.llm_client.provider.upper()} | {self.agent.llm_client.model}",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=TEXT_DIM
        )
        self.status_provider.pack(side="left", padx=12)

        self.status_memory = ctk.CTkLabel(
            self.status_bar,
            text="Memory: —",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=TEXT_DIM
        )
        self.status_memory.pack(side="left", padx=12)

        self.status_uptime = ctk.CTkLabel(
            self.status_bar,
            text="Uptime: 0m",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=TEXT_DIM
        )
        self.status_uptime.pack(side="right", padx=12)

    # ═══════════════════════════════════════
    # VIEWS
    # ═══════════════════════════════════════

    def _create_chat_view(self):
        """Main chat view with waveform, chat feed, quick actions, and input."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.views["chat"] = frame

        # Waveform visualizer
        wave_container = ctk.CTkFrame(frame, height=44, fg_color="transparent")
        wave_container.pack(fill="x", padx=14, pady=(8, 4))

        self.wave_canvas = tk.Canvas(wave_container, height=40, bg=BG_DEEP, highlightthickness=0)
        self.wave_canvas.pack(fill="x", expand=True)

        # Chat feed
        self.chat_frame = ctk.CTkScrollableFrame(
            frame, corner_radius=10, fg_color=BG_SURFACE,
            border_width=1, border_color=BORDER_GLOW
        )
        self.chat_frame.pack(fill="both", expand=True, padx=14, pady=4)

        # Quick action pills
        pills_container = ctk.CTkScrollableFrame(frame, height=36, orientation="horizontal", fg_color="transparent")
        pills_container.pack(fill="x", padx=12, pady=(4, 2))

        pills = [
            ("📸 Screenshot", "Take a screenshot"),
            ("🔊 Mute", "Mute system audio"),
            ("🔋 Battery", "Check my battery percentage"),
            ("⚡ System", "Get system stats"),
            ("📝 Note", "Save a note 'Quick Note' with content 'Review tasks'"),
            ("📁 Files", "Search for files on my computer"),
            ("⛅ Weather", "What is the weather today?"),
        ]
        for label, cmd in pills:
            ctk.CTkButton(
                pills_container, text=label,
                font=ctk.CTkFont(family="Inter", size=11),
                fg_color="#1e293b", hover_color="#334155",
                text_color=TEXT_PRIMARY,
                border_width=1, border_color="#334155",
                height=26, corner_radius=13,
                command=lambda c=cmd: self._process_user_query(c)
            ).pack(side="left", padx=3)

        # Input deck
        deck = ctk.CTkFrame(frame, fg_color="transparent")
        deck.pack(fill="x", padx=14, pady=(4, 10))

        self.mic_btn = ctk.CTkButton(
            deck, text="🎙️", width=44, height=44, corner_radius=22,
            fg_color=ACCENT_CYAN, hover_color="#0ea5e9",
            text_color="#000000", font=ctk.CTkFont(size=18),
            command=self._toggle_voice_input
        )
        self.mic_btn.pack(side="left", padx=(0, 8))

        self.text_entry = ctk.CTkEntry(
            deck,
            placeholder_text=f"Type a command or say 'Hey {Config.ASSISTANT_NAME}'...",
            placeholder_text_color=TEXT_DIM,
            font=ctk.CTkFont(family="Inter", size=12),
            height=44, corner_radius=22,
            fg_color="#182234", border_color="#22334e", border_width=1,
            text_color="#ffffff"
        )
        self.text_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.text_entry.bind("<Return>", lambda e: self._on_send_clicked())

        self.send_btn = ctk.CTkButton(
            deck, text="➔", width=44, height=44, corner_radius=22,
            fg_color="#1e293b", hover_color="#334155",
            border_width=1, border_color=ACCENT_CYAN,
            font=ctk.CTkFont(family="JetBrains Mono", size=16, weight="bold"),
            text_color=ACCENT_CYAN,
            command=self._on_send_clicked
        )
        self.send_btn.pack(side="right")

    def _create_home_view(self):
        """Home dashboard with stats cards and welcome."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.views["home"] = frame

        # Welcome header
        ctk.CTkLabel(
            frame,
            text=f"Welcome to {Config.ASSISTANT_NAME}",
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(padx=20, pady=(20, 4))

        ctk.CTkLabel(
            frame,
            text=datetime.now().strftime("%A, %B %d, %Y"),
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=TEXT_SECONDARY
        ).pack(padx=20, pady=(0, 16))

        # Stats cards grid
        cards_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=4)
        cards_frame.grid_columnconfigure((0, 1), weight=1)

        card_data = [
            ("🔋 Battery", "battery_card", ACCENT_EMERALD),
            ("⚡ CPU", "cpu_card", ACCENT_CYAN),
            ("💾 RAM", "ram_card", ACCENT_PURPLE),
            ("💿 Disk", "disk_card", ACCENT_AMBER),
        ]

        self.home_cards = {}
        for i, (title, key, color) in enumerate(card_data):
            card = ctk.CTkFrame(cards_frame, corner_radius=12, fg_color=BG_SURFACE,
                                border_width=1, border_color=BORDER_GLOW)
            card.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="nsew")

            ctk.CTkLabel(
                card, text=title,
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                text_color=color
            ).pack(padx=16, pady=(14, 2), anchor="w")

            value_lbl = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(family="JetBrains Mono", size=22, weight="bold"),
                text_color=TEXT_PRIMARY
            )
            value_lbl.pack(padx=16, pady=(2, 14), anchor="w")
            self.home_cards[key] = value_lbl

    def _create_memory_view(self):
        """Memory browser — view stored memories, profile, and stats."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.views["memory"] = frame

        ctk.CTkLabel(
            frame,
            text="🧠 Memory Bank",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(padx=20, pady=(20, 10))

        # Memory stats
        self.memory_stats_frame = ctk.CTkFrame(frame, corner_radius=10, fg_color=BG_SURFACE,
                                                border_width=1, border_color=BORDER_GLOW)
        self.memory_stats_frame.pack(fill="x", padx=20, pady=4)

        self.memory_stats_lbl = ctk.CTkLabel(
            self.memory_stats_frame,
            text="Loading memory stats...",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=TEXT_SECONDARY,
            justify="left"
        )
        self.memory_stats_lbl.pack(padx=16, pady=14, anchor="w")

        # Recent conversations
        ctk.CTkLabel(
            frame,
            text="Recent Conversations",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=TEXT_SECONDARY
        ).pack(padx=20, pady=(16, 4), anchor="w")

        self.memory_list = ctk.CTkScrollableFrame(frame, fg_color=BG_SURFACE,
                                                    corner_radius=10, border_width=1, border_color=BORDER_GLOW)
        self.memory_list.pack(fill="both", expand=True, padx=20, pady=(4, 10))

        # Clear memory button
        ctk.CTkButton(
            frame,
            text="🗑️ Clear All Memories",
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color="#450a0a", hover_color="#7f1d1d",
            text_color=ACCENT_RED,
            height=36, corner_radius=10,
            command=self._clear_memory
        ).pack(padx=20, pady=(0, 12))

    def _create_system_view(self):
        """System monitor with live gauges."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.views["system"] = frame

        ctk.CTkLabel(
            frame,
            text="📊 System Monitor",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(padx=20, pady=(20, 10))

        self.system_details = ctk.CTkLabel(
            frame,
            text="Loading system info...",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=500
        )
        self.system_details.pack(padx=20, pady=10, anchor="w")

    def _create_settings_view(self):
        """In-app settings (read-only display of current config)."""
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.views["settings"] = frame

        ctk.CTkLabel(
            frame,
            text="⚙️ Settings",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(padx=20, pady=(20, 10))

        settings_info = f"""LLM Provider:   {Config.LLM_PROVIDER}
LLM Model:      {Config.LLM_MODEL}
TTS Engine:     {Config.TTS_ENGINE}
STT Engine:     {Config.STT_ENGINE}
Nickname:       {Config.ASSISTANT_NAME}
Wake Word:      {Config.WAKE_WORD}
Memory:         {'Enabled' if Config.ENABLE_MEMORY else 'Disabled'}
Voice Feedback: {'On' if Config.ENABLE_VOICE_FEEDBACK else 'Off'}
Operation Mode: {Config.OPERATION_MODE}"""

        settings_card = ctk.CTkFrame(frame, corner_radius=10, fg_color=BG_SURFACE,
                                      border_width=1, border_color=BORDER_GLOW)
        settings_card.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            settings_card,
            text=settings_info,
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=TEXT_SECONDARY,
            justify="left"
        ).pack(padx=16, pady=16, anchor="w")

        ctk.CTkLabel(
            frame,
            text="Edit your .env file to change settings, then restart.",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=TEXT_DIM
        ).pack(padx=20, pady=(4, 10))

    # ═══════════════════════════════════════
    # VIEW SWITCHING
    # ═══════════════════════════════════════

    def _switch_view(self, view_id: str):
        """Switch to a different sidebar view."""
        # Hide all views
        for v in self.views.values():
            v.pack_forget()

        # Show selected view
        if view_id in self.views:
            self.views[view_id].pack(fill="both", expand=True)

        # Update sidebar button highlights
        for vid, btn in self.nav_buttons.items():
            btn.configure(fg_color=SIDEBAR_ACTIVE if vid == view_id else "transparent")

        self.current_view = view_id

        # Refresh view-specific data
        if view_id == "memory":
            self._refresh_memory_view()
        elif view_id == "system":
            self._refresh_system_view()
        elif view_id == "home":
            self._refresh_home_view()

    def _refresh_memory_view(self):
        """Refresh the memory browser with latest data."""
        if not self.agent.memory:
            self.memory_stats_lbl.configure(text="Memory is disabled. Set ENABLE_MEMORY=true in .env")
            return

        def _load():
            stats = self.agent.memory.get_stats()
            recent = self.agent.memory.get_recent_conversations(limit=10)

            stats_text = (
                f"Total Conversations: {stats.get('total_conversations', 0)}\n"
                f"Vector Entries:      {stats.get('vector_entries', 0)}\n"
                f"Profile Facts:       {stats.get('profile_facts', 0)}\n"
                f"Profile Preferences: {stats.get('profile_preferences', 0)}\n"
                f"First Memory:        {stats.get('first_memory', 'None')[:19]}\n"
                f"Last Memory:         {stats.get('last_memory', 'None')[:19]}"
            )

            def _update():
                if hasattr(self, "memory_stats_lbl") and self.memory_stats_lbl.winfo_exists():
                    self.memory_stats_lbl.configure(text=stats_text)

                if hasattr(self, "memory_list") and self.memory_list.winfo_exists():
                    for widget in self.memory_list.winfo_children():
                        widget.destroy()

                    if not recent:
                        ctk.CTkLabel(
                            self.memory_list, text="No conversations stored yet.",
                            font=ctk.CTkFont(family="Inter", size=12),
                            text_color=TEXT_DIM
                        ).pack(padx=12, pady=12)
                    else:
                        for conv in recent:
                            card = ctk.CTkFrame(self.memory_list, fg_color=BG_DEEP, corner_radius=8)
                            card.pack(fill="x", padx=4, pady=3)

                            ts = conv.get("timestamp", "")[:16].replace("T", " ")
                            q = conv.get("user_input", "")[:80]
                            a = conv.get("assistant_response", "")[:80]

                            ctk.CTkLabel(
                                card, text=f"📅 {ts}",
                                font=ctk.CTkFont(family="JetBrains Mono", size=10),
                                text_color=TEXT_DIM
                            ).pack(padx=10, pady=(6, 0), anchor="w")

                            ctk.CTkLabel(
                                card, text=f"👤 {q}",
                                font=ctk.CTkFont(family="Inter", size=11),
                                text_color=TEXT_PRIMARY, wraplength=400, justify="left"
                            ).pack(padx=10, pady=(2, 0), anchor="w")

                            ctk.CTkLabel(
                                card, text=f"🤖 {a}",
                                font=ctk.CTkFont(family="Inter", size=11),
                                text_color=TEXT_SECONDARY, wraplength=400, justify="left"
                            ).pack(padx=10, pady=(0, 6), anchor="w")

            self.after(0, _update)

        threading.Thread(target=_load, daemon=True).start()

    def _refresh_system_view(self):
        """Refresh system monitor data."""
        def _load():
            stats = get_system_stats()
            bat = get_battery_status()

            lines = []
            if stats.get("success"):
                lines.append(f"CPU Usage:     {stats.get('cpu_usage_percent', 0)}%")
                lines.append(f"RAM Usage:     {stats.get('ram_percent', 0)}%  ({stats.get('ram_used_gb', 0):.1f} / {stats.get('ram_total_gb', 0):.1f} GB)")
                lines.append(f"Disk Usage:    {stats.get('disk_percent', 0)}%  ({stats.get('disk_used_gb', 0):.0f} / {stats.get('disk_total_gb', 0):.0f} GB)")

            if bat.get("success"):
                lines.append(f"Battery:       {bat.get('percent', '?')}%  {'(Plugged In)' if bat.get('power_plugged') else '(On Battery)'}")

            def _update():
                if hasattr(self, "system_details") and self.system_details.winfo_exists():
                    self.system_details.configure(text="\n".join(lines) if lines else "Could not retrieve system info.")

            self.after(0, _update)

        threading.Thread(target=_load, daemon=True).start()

    def _refresh_home_view(self):
        """Refresh home dashboard cards."""
        def _load():
            stats = get_system_stats()
            bat = get_battery_status()

            def _update():
                if hasattr(self, "home_cards"):
                    if bat.get("success") and "battery_card" in self.home_cards:
                        self.home_cards["battery_card"].configure(text=f"{bat.get('percent', '?')}%")
                    if stats.get("success"):
                        if "cpu_card" in self.home_cards:
                            self.home_cards["cpu_card"].configure(text=f"{stats.get('cpu_usage_percent', 0)}%")
                        if "ram_card" in self.home_cards:
                            self.home_cards["ram_card"].configure(text=f"{stats.get('ram_percent', 0)}%")
                        if "disk_card" in self.home_cards:
                            self.home_cards["disk_card"].configure(text=f"{stats.get('disk_percent', 0)}%")

            self.after(0, _update)

        threading.Thread(target=_load, daemon=True).start()

    def _clear_memory(self):
        """Clear all stored memories after confirmation."""
        from quadroid.ui.confirm import request_confirmation
        def _do_clear():
            approved = request_confirmation(
                "Clear Memory",
                "This will permanently delete ALL stored conversations, vectors, and learned preferences.\n\nAre you sure?",
                action_type="danger"
            )
            if approved and self.agent.memory:
                self.agent.memory.clear_all()
                self.after(0, self._refresh_memory_view)

        threading.Thread(target=_do_clear, daemon=True).start()

    # ═══════════════════════════════════════
    # ANIMATIONS & TELEMETRY
    # ═══════════════════════════════════════

    def _animate_waveform(self):
        """Dynamic waveform animation on the chat view."""
        if self.current_view != "chat":
            self.after(60, self._animate_waveform)
            return

        self.wave_canvas.delete("all")
        width = self.wave_canvas.winfo_width()
        height = 40

        if width > 10:
            center_x = width / 2
            center_y = height / 2
            num_bars = 32
            bar_spacing = max(4, min(7, width // (num_bars + 4)))
            start_x = center_x - (num_bars * bar_spacing) / 2

            color = ACCENT_CYAN
            multiplier = 1.0
            if self.is_listening:
                color = ACCENT_RED
                multiplier = 2.4
            elif self.is_processing:
                color = ACCENT_PURPLE
                multiplier = 1.8

            for i in range(num_bars):
                dist = abs(i - num_bars / 2) / (num_bars / 2)
                base_h = math.sin(self.anim_phase + i * 0.4) * (12 * multiplier) * (1 - dist * 0.6)
                h = max(2, abs(base_h))
                x = start_x + i * bar_spacing

                self.wave_canvas.create_line(
                    x, center_y - h, x, center_y + h,
                    fill=color, width=2, capstyle=tk.ROUND
                )

        self.anim_phase += 0.15
        self.after(40, self._animate_waveform)

    def _start_telemetry_loop(self):
        """Update CPU/RAM in the header every 4 seconds."""
        def _update():
            stats = get_system_stats()
            if stats.get("success"):
                cpu = stats.get("cpu_usage_percent", 0)
                ram = stats.get("ram_percent", 0)
                def _apply():
                    if hasattr(self, "cpu_lbl") and self.cpu_lbl.winfo_exists():
                        self.cpu_lbl.configure(text=f"CPU {cpu}%")
                        self.ram_lbl.configure(text=f"RAM {ram}%")
                self.after(0, _apply)
            self.after(4000, self._start_telemetry_loop)

        threading.Thread(target=_update, daemon=True).start()

    def _update_status_bar(self):
        """Update status bar info every 10 seconds."""
        # Uptime
        elapsed = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed, 3600)
        minutes = remainder // 60
        uptime_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
        if hasattr(self, "status_uptime") and self.status_uptime.winfo_exists():
            self.status_uptime.configure(text=f"Uptime: {uptime_str}")

        # Memory count
        if self.agent.memory:
            def _check_mem():
                try:
                    stats = self.agent.memory.get_stats()
                    count = stats.get("total_conversations", 0)
                    def _apply():
                        if hasattr(self, "status_memory") and self.status_memory.winfo_exists():
                            self.status_memory.configure(text=f"Memory: {count} entries")
                    self.after(0, _apply)
                except Exception:
                    pass
            threading.Thread(target=_check_mem, daemon=True).start()

        self.after(10000, self._update_status_bar)

    # ═══════════════════════════════════════
    # CHAT & MESSAGING
    # ═══════════════════════════════════════

    def _append_message(self, sender: str, text: str, is_user: bool = False):
        """Add a styled message card to the chat feed."""
        def _insert():
            card = ctk.CTkFrame(
                self.chat_frame, corner_radius=10,
                fg_color="#1a2332" if is_user else BG_DEEP,
                border_width=1,
                border_color=ACCENT_CYAN if is_user else BORDER_GLOW
            )
            card.pack(
                anchor="e" if is_user else "w",
                padx=8, pady=4, fill="none"
            )

            # Sender label
            icon = "👤" if is_user else "◆"
            color = ACCENT_CYAN if is_user else ACCENT_EMERALD

            ctk.CTkLabel(
                card,
                text=f"{icon} {sender}",
                font=ctk.CTkFont(family="JetBrains Mono", size=10, weight="bold"),
                text_color=color
            ).pack(anchor="w", padx=12, pady=(8, 0))

            # Message content
            ctk.CTkLabel(
                card,
                text=text,
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=TEXT_PRIMARY,
                wraplength=420,
                justify="left"
            ).pack(padx=12, pady=(2, 10))

        self.after(0, _insert)

    def _append_action_chip(self, tool_name: str, args: dict):
        """Display a tool execution chip in the chat feed."""
        def _insert():
            display_args = ", ".join(f"{k}={v}" for k, v in args.items()) if args else ""
            action_text = f"⚙️ {tool_name}({display_args})"

            ctk.CTkLabel(
                self.chat_frame,
                text=action_text,
                font=ctk.CTkFont(family="JetBrains Mono", size=10),
                text_color=ACCENT_CYAN,
                fg_color="#082f49",
                corner_radius=6, padx=10, pady=4
            ).pack(anchor="w", padx=12, pady=2)

        self.after(0, _insert)

    def _append_typing_indicator(self):
        """Show a typing/thinking indicator."""
        self._typing_label = ctk.CTkLabel(
            self.chat_frame,
            text="◆ thinking ● ● ●",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=ACCENT_PURPLE
        )
        self._typing_label.pack(anchor="w", padx=12, pady=4)

    def _remove_typing_indicator(self):
        """Remove the typing indicator."""
        if hasattr(self, "_typing_label") and self._typing_label.winfo_exists():
            self._typing_label.destroy()

    def _on_tool_action(self, tool_name: str, args: dict):
        self._append_action_chip(tool_name, args)

    # ═══════════════════════════════════════
    # USER INPUT
    # ═══════════════════════════════════════

    def _on_send_clicked(self):
        text = self.text_entry.get().strip()
        if not text or self.is_processing:
            return
        self.text_entry.delete(0, "end")
        self._process_user_query(text)

    def _process_user_query(self, user_query: str):
        """Process user input through the agent pipeline."""
        self.is_processing = True

        # Switch to chat view if not already there
        if self.current_view != "chat":
            self._switch_view("chat")

        self._append_message("YOU", user_query, is_user=True)
        self.after(0, self._append_typing_indicator)

        def _worker():
            try:
                play_sound_async("interface.mp3")
                result = self.agent.process_input(user_query)
                reply = result.get("response", "Task completed.")

                self.after(0, self._remove_typing_indicator)
                self._append_message(Config.ASSISTANT_NAME.upper(), reply, is_user=False)

                if Config.ENABLE_VOICE_FEEDBACK:
                    speak(reply, async_mode=True)

            except Exception as e:
                self.after(0, self._remove_typing_indicator)
                self._append_message(Config.ASSISTANT_NAME.upper(), f"⚠️ Error: {str(e)}", is_user=False)
            finally:
                self.is_processing = False

        threading.Thread(target=_worker, daemon=True).start()

    def _toggle_voice_input(self):
        """Trigger microphone speech recognition."""
        if self.is_listening or self.is_processing:
            return

        def _listen_worker():
            self.is_listening = True
            self.after(0, lambda: self.mic_btn.configure(fg_color=ACCENT_RED))

            play_sound_async("wake-up.mp3")
            transcript = listen_and_transcribe(timeout=5.0, phrase_time_limit=10.0)

            self.after(0, lambda: self.mic_btn.configure(fg_color=ACCENT_CYAN))
            self.is_listening = False

            if transcript:
                self._process_user_query(transcript)

        threading.Thread(target=_listen_worker, daemon=True).start()

    # ═══════════════════════════════════════
    # WAKE WORD, TRAY, MINI-MODE
    # ═══════════════════════════════════════

    def _on_wake_word_triggered(self):
        """Called when user says the wake word."""
        self.after(0, self._bring_to_front)
        self._toggle_voice_input()

    def _bring_to_front(self):
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after_idle(self.attributes, "-topmost", False)

    def _minimize_to_tray(self):
        """Minimize to system tray instead of closing."""
        self.withdraw()

    def _toggle_mini_mode(self):
        """Toggle the floating mini-mode orb overlay."""
        if self.mini_window and self.mini_window.winfo_exists():
            self.mini_window.destroy()
            self.mini_window = None
            self.deiconify()
        else:
            self.withdraw()
            self.mini_window = MiniModeWindow(
                self,
                on_expand=lambda: self.after(0, self._exit_mini_mode),
                on_mic=lambda: self._toggle_voice_input()
            )

    def _exit_mini_mode(self):
        """Exit mini-mode and restore full window."""
        if self.mini_window and self.mini_window.winfo_exists():
            self.mini_window.destroy()
            self.mini_window = None
        self.deiconify()
        self._bring_to_front()

    def _on_quit(self):
        """Cleanly quit the application."""
        if self.tray:
            self.tray.stop()
        if self.mini_window and self.mini_window.winfo_exists():
            self.mini_window.destroy()
        self.destroy()
        sys.exit(0)


def launch_gui():
    """Launch the Quadroid Desktop Application."""
    app = QuadroidApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
