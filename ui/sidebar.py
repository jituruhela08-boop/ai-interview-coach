"""
ui/sidebar.py — Premium Animated Sidebar Navigation
Glassmorphism sidebar with icon+label nav items, active glow state,
and collapsible sections.
"""

import tkinter as tk
from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from config import Colors, Fonts, Layout


# ─────────────────────────────────────────────
#  NAV ITEM  (single sidebar entry)
# ─────────────────────────────────────────────
class SidebarItem(ctk.CTkFrame):
    def __init__(self, master, icon: str, label: str,
                 page_key: str, on_click: Callable, **kwargs):
        super().__init__(master,
                          fg_color="transparent",
                          corner_radius=10,
                          cursor="hand2",
                          **kwargs)
        self.page_key  = page_key
        self.on_click  = on_click
        self._active   = False

        self._icon_lbl = ctk.CTkLabel(
            self, text=icon,
            font=ctk.CTkFont(size=18),
            text_color=Colors.TEXT_MUTED,
            width=30,
        )
        self._icon_lbl.pack(side="left", padx=(12, 0), pady=10)

        self._text_lbl = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(*Fonts.NAV_ITEM),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        )
        self._text_lbl.pack(side="left", padx=10, fill="x", expand=True)

        # Active indicator strip (left edge)
        self._indicator = tk.Frame(self, width=3,
                                    bg=Colors.BG_SECONDARY)
        self._indicator.place(relx=0, rely=0, relheight=1, width=3)

        # Bind click on all children
        for w in [self, self._icon_lbl, self._text_lbl]:
            w.bind("<Button-1>", self._handle_click)
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(fg_color=Colors.SIDEBAR_ACTIVE)
            self._icon_lbl.configure(text_color=Colors.NEON_CYAN)
            self._text_lbl.configure(
                text_color=Colors.TEXT_PRIMARY,
                font=ctk.CTkFont(*Fonts.NAV_ITEM_ACTIVE)
            )
            self._indicator.configure(bg=Colors.NEON_CYAN)
        else:
            self.configure(fg_color="transparent")
            self._icon_lbl.configure(text_color=Colors.TEXT_MUTED)
            self._text_lbl.configure(
                text_color=Colors.TEXT_SECONDARY,
                font=ctk.CTkFont(*Fonts.NAV_ITEM)
            )
            self._indicator.configure(bg=Colors.BG_SECONDARY)

    def _on_enter(self, _):
        if not self._active:
            self.configure(fg_color=Colors.SIDEBAR_HOVER)

    def _on_leave(self, _):
        if not self._active:
            self.configure(fg_color="transparent")

    def _handle_click(self, _):
        self.on_click(self.page_key)


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
NAV_ITEMS: List[Dict] = [
    {"icon": "⌂",  "label": "Dashboard",       "key": "home"},
    {"icon": "📄",  "label": "Resume Analyzer",  "key": "resume"},
    {"icon": "🎙",  "label": "AI Interview",     "key": "interview"},
    {"icon": "🗺",  "label": "Learning Roadmap", "key": "roadmap"},
    {"icon": "📊",  "label": "Analytics",        "key": "analytics"},
    {"icon": "📋",  "label": "Reports",          "key": "reports"},
    {"icon": "⚙",  "label": "Settings",         "key": "settings"},
]


class Sidebar(ctk.CTkFrame):
    """
    Full-height sidebar with logo, nav items, and bottom user card.
    """
    def __init__(self, master, navigate_callback: Callable,
                 user_name: str = "User", **kwargs):
        super().__init__(
            master,
            width=Layout.SIDEBAR_WIDTH,
            fg_color=Colors.SIDEBAR_BG,
            corner_radius=0,
            **kwargs
        )
        self.pack_propagate(False)
        self._navigate = navigate_callback
        self._items: Dict[str, SidebarItem] = {}
        self._active_key: Optional[str] = None

        self._build_logo()
        self._build_nav()
        self._build_user_card(user_name)

    # ─────────────────────────────────────────
    def _build_logo(self):
        logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=80)
        logo_frame.pack(fill="x", pady=(10, 0))
        logo_frame.pack_propagate(False)

        # Gradient canvas for logo area
        canvas = tk.Canvas(logo_frame, width=Layout.SIDEBAR_WIDTH, height=80,
                            bg=Colors.SIDEBAR_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Glow circle behind icon
        canvas.create_oval(18, 18, 54, 54,
                            fill=f"{Colors.NEON_CYAN}18", outline=Colors.NEON_CYAN,
                            width=1)
        canvas.create_text(36, 36, text="🤖", font=("Arial", 16))

        # App name
        canvas.create_text(
            70, 26, anchor="w",
            text="AI Interview",
            font=(Fonts.FAMILY_PRIMARY, 13, Fonts.BOLD),
            fill=Colors.TEXT_PRIMARY
        )
        canvas.create_text(
            70, 46, anchor="w",
            text="Coach",
            font=(Fonts.FAMILY_PRIMARY, 11, Fonts.NORMAL),
            fill=Colors.NEON_CYAN
        )

        # Separator line with gradient
        sep = ctk.CTkFrame(self, height=1, fg_color=Colors.BORDER_DIM)
        sep.pack(fill="x", padx=16, pady=(4, 0))

    def _build_nav(self):
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Nav label
        ctk.CTkLabel(
            nav_frame, text="NAVIGATION",
            font=ctk.CTkFont(*Fonts.CAPTION),
            text_color=Colors.TEXT_MUTED,
        ).pack(anchor="w", padx=12, pady=(8, 4))

        for item_def in NAV_ITEMS:
            item = SidebarItem(
                nav_frame,
                icon=item_def["icon"],
                label=item_def["label"],
                page_key=item_def["key"],
                on_click=self._on_item_click,
            )
            item.pack(fill="x", pady=2)
            self._items[item_def["key"]] = item

    def _build_user_card(self, user_name: str):
        sep = ctk.CTkFrame(self, height=1, fg_color=Colors.BORDER_DIM)
        sep.pack(fill="x", padx=16)

        card = ctk.CTkFrame(self, fg_color="transparent", height=70)
        card.pack(fill="x", padx=12, pady=10)
        card.pack_propagate(False)

        # Avatar circle
        av_canvas = tk.Canvas(card, width=38, height=38,
                               bg=Colors.SIDEBAR_BG, highlightthickness=0)
        av_canvas.pack(side="left", padx=(4, 10), pady=6)
        av_canvas.create_oval(2, 2, 36, 36,
                               fill=Colors.NEON_PURPLE + "40",
                               outline=Colors.NEON_PURPLE, width=1)
        av_canvas.create_text(20, 20, text=user_name[0].upper(),
                               font=(Fonts.FAMILY_PRIMARY, 14, Fonts.BOLD),
                               fill=Colors.NEON_PURPLE)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="y", pady=6)
        self._name_label = ctk.CTkLabel(
            info, text=user_name,
            font=ctk.CTkFont(*Fonts.BODY_BOLD),
            text_color=Colors.TEXT_PRIMARY, anchor="w",
        )
        self._name_label.pack(anchor="w")
        ctk.CTkLabel(
            info, text="Premium Member",
            font=ctk.CTkFont(*Fonts.CAPTION),
            text_color=Colors.NEON_CYAN, anchor="w",
        ).pack(anchor="w")

    # ─────────────────────────────────────────
    def _on_item_click(self, key: str):
        if self._active_key:
            self._items[self._active_key].set_active(False)
        self._active_key = key
        self._items[key].set_active(True)
        self._navigate(key)

    def set_active(self, key: str):
        if self._active_key and self._active_key in self._items:
            self._items[self._active_key].set_active(False)
        self._active_key = key
        if key in self._items:
            self._items[key].set_active(True)

    def update_user_name(self, name: str):
        self._name_label.configure(text=name)