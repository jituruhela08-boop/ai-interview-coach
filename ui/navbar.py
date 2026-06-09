"""
ui/navbar.py — Top Navigation Bar
Search bar, notification bell, settings icon, user avatar, page breadcrumb.
"""

import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from config import Colors, Fonts, Layout
from ui.components import NeonEntry, Toast


class Navbar(ctk.CTkFrame):
    """
    Full-width top navbar with:
    - Page title / breadcrumb (left)
    - Search bar (center)
    - Icon buttons: notifications, settings (right)
    - User avatar chip (right)
    """

    PAGE_TITLES = {
        "home":      ("⌂  Dashboard",       "Your career intelligence at a glance"),
        "resume":    ("📄  Resume Analyzer",  "Upload and analyze your resume"),
        "interview": ("🎙  AI Interview",     "Practice with AI-powered mock interviews"),
        "roadmap":   ("🗺  Learning Roadmap", "Personalized skill-building plan"),
        "analytics": ("📊  Analytics",        "Performance trends and insights"),
        "reports":   ("📋  Reports",          "Export and share your progress"),
        "settings":  ("⚙  Settings",         "Configure your profile and API keys"),
    }

    def __init__(self, master, user_name: str = "User",
                 on_settings: Callable = None,
                 on_search: Callable = None,
                 **kwargs):
        super().__init__(
            master,
            height=Layout.NAVBAR_HEIGHT,
            fg_color=Colors.BG_SECONDARY,
            corner_radius=0,
            border_width=0,
            **kwargs
        )
        self.pack_propagate(False)
        self._user_name     = user_name
        self._on_settings   = on_settings
        self._on_search     = on_search
        self._notif_count   = 0

        self._build()

    def _build(self):
        # Left: breadcrumb
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(20, 0))

        self._page_title = ctk.CTkLabel(
            left, text="⌂  Dashboard",
            font=ctk.CTkFont(*Fonts.SECTION_TITLE),
            text_color=Colors.TEXT_PRIMARY,
        )
        self._page_title.pack(anchor="w", pady=(12, 0))

        self._page_sub = ctk.CTkLabel(
            left, text="Your career intelligence at a glance",
            font=ctk.CTkFont(*Fonts.CAPTION),
            text_color=Colors.TEXT_MUTED,
        )
        self._page_sub.pack(anchor="w")

        # Right: action icons
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", fill="y", padx=(0, 20))

        # User chip
        self._user_chip = ctk.CTkFrame(
            right, fg_color=Colors.BG_CARD,
            corner_radius=20, border_width=1,
            border_color=Colors.BORDER_GLOW, cursor="hand2",
        )
        self._user_chip.pack(side="right", padx=(8, 0), pady=12)
        ctk.CTkLabel(
            self._user_chip,
            text=self._user_name[0].upper(),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Colors.NEON_PURPLE,
            fg_color=Colors.NEON_PURPLE + "30",
            corner_radius=14,
            width=28, height=28,
        ).pack(side="left", padx=(6, 4), pady=6)
        self._user_name_lbl = ctk.CTkLabel(
            self._user_chip, text=self._user_name,
            font=ctk.CTkFont(*Fonts.LABEL),
            text_color=Colors.TEXT_PRIMARY,
        )
        self._user_name_lbl.pack(side="left", padx=(0, 10))

        # Settings button
        self._settings_btn = ctk.CTkButton(
            right, text="⚙",
            width=36, height=36,
            fg_color=Colors.BG_CARD,
            hover_color=Colors.BG_CARD_HOVER,
            border_color=Colors.BORDER_GLOW,
            border_width=1,
            corner_radius=8,
            text_color=Colors.TEXT_SECONDARY,
            font=ctk.CTkFont(size=16),
            command=self._on_settings,
        )
        self._settings_btn.pack(side="right", padx=4, pady=14)

        # Notification button
        notif_frame = ctk.CTkFrame(right, fg_color="transparent")
        notif_frame.pack(side="right", padx=4, pady=14)

        self._notif_btn = ctk.CTkButton(
            notif_frame, text="🔔",
            width=36, height=36,
            fg_color=Colors.BG_CARD,
            hover_color=Colors.BG_CARD_HOVER,
            border_color=Colors.BORDER_GLOW,
            border_width=1,
            corner_radius=8,
            text_color=Colors.TEXT_SECONDARY,
            font=ctk.CTkFont(size=16),
            command=self._show_notifications,
        )
        self._notif_btn.pack()

        # Center: search
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.pack(fill="x", expand=True, padx=20, pady=12)

        search_frame = ctk.CTkFrame(
            center,
            fg_color=Colors.BG_INPUT,
            corner_radius=Layout.INPUT_CORNER_RADIUS,
            border_width=1,
            border_color=Colors.BORDER_GLOW,
            height=36,
        )
        search_frame.pack(expand=True, fill="x", padx=60)
        search_frame.pack_propagate(False)

        ctk.CTkLabel(
            search_frame, text="🔍",
            font=ctk.CTkFont(size=14),
            text_color=Colors.TEXT_MUTED,
        ).pack(side="left", padx=10)

        self._search_var = tk.StringVar()
        self._search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text="Search features, skills, history…",
            placeholder_text_color=Colors.TEXT_MUTED,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            font=ctk.CTkFont(*Fonts.BODY),
        )
        self._search_entry.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._search_entry.bind("<Return>", self._on_search_submit)

        # Bottom separator
        sep = tk.Frame(self, height=1, bg=Colors.BORDER_DIM)
        sep.place(relx=0, rely=1.0, relwidth=1, anchor="sw")

    # ─────────────────────────────────────────
    def update_page(self, key: str):
        title, sub = self.PAGE_TITLES.get(key, (key.title(), ""))
        self._page_title.configure(text=title)
        self._page_sub.configure(text=sub)

    def update_user(self, name: str):
        self._user_name = name
        self._user_name_lbl.configure(text=name)

    def _on_search_submit(self, _):
        query = self._search_var.get().strip()
        if query and self._on_search:
            self._on_search(query)

    def _show_notifications(self):
        Toast(self.winfo_toplevel(),
              "No new notifications — you're all caught up! ✓",
              kind="info")