"""
ui/sidebar.py
Premium dark glassmorphism sidebar navigation for AI Interview Coach.
"""
import customtkinter as ctk
from config import Colors, Layout, APP_NAME, APP_VERSION


class Sidebar(ctk.CTkFrame):
    """
    Fixed-width sidebar with neon icon buttons and active state highlighting.
    Calls navigate_callback(page_name) when a nav item is clicked.
    """

    NAV_ITEMS = [
        ("home",      "⌂",  "Dashboard"),
        ("resume",    "◈",  "Resume Analyzer"),
        ("interview", "◉",  "Mock Interview"),
        ("analytics", "◎",  "Analytics"),
        ("roadmap",   "◆",  "Roadmap"),
        ("settings",  "⚙",  "Settings"),
    ]

    def __init__(self, parent, navigate_callback, **kwargs):
        super().__init__(
            parent,
            width         = Layout.SIDEBAR_WIDTH,
            fg_color      = Colors.SIDEBAR_BG,
            corner_radius = 0,
            border_width  = 0,
            **kwargs
        )
        self.navigate_callback = navigate_callback
        self.active_page       = "home"
        self._buttons          = {}

        self.pack_propagate(False)
        self._build()

    # ── build ─────────────────────────────────────────────────────────────────
    def _build(self):
        # Logo / brand area
        logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=72)
        logo_frame.pack(fill="x", padx=0, pady=0)
        logo_frame.pack_propagate(False)

        # Glowing accent line at top
        top_accent = ctk.CTkFrame(self, height=2, fg_color=Colors.NEON_CYAN, corner_radius=0)
        top_accent.pack(fill="x")

        # App name
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            brand_frame,
            text       = "◈ AI Coach",
            text_color = Colors.NEON_CYAN,
            font       = ("Segoe UI", 15, "bold"),
            anchor     = "w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_frame,
            text       = f"v{APP_VERSION} · Gemini AI",
            text_color = Colors.TEXT_MUTED,
            font       = ("Segoe UI", 10, "normal"),
            anchor     = "w",
        ).pack(anchor="w")

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=Colors.BORDER_DIM, corner_radius=0).pack(fill="x")

        # Section label
        ctk.CTkLabel(
            self,
            text       = "  NAVIGATION",
            text_color = Colors.TEXT_MUTED,
            font       = ("Segoe UI", 9, "bold"),
            anchor     = "w",
        ).pack(fill="x", padx=16, pady=(16, 4))

        # Nav items
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=0)

        for page, icon, label in self.NAV_ITEMS:
            btn = self._make_nav_button(nav_frame, page, icon, label)
            btn.pack(fill="x", pady=2)
            self._buttons[page] = btn

        # Spacer
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        # Bottom: status indicator
        ctk.CTkFrame(self, height=1, fg_color=Colors.BORDER_DIM, corner_radius=0).pack(fill="x")
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(fill="x", padx=16, pady=12)

        self.status_dot = ctk.CTkLabel(
            status_frame, text="●",
            text_color = Colors.NEON_GREEN,
            font       = ("Segoe UI", 10),
        )
        self.status_dot.pack(side="left")

        self.status_label = ctk.CTkLabel(
            status_frame, text=" Ready",
            text_color = Colors.TEXT_MUTED,
            font       = ("Segoe UI", 10),
        )
        self.status_label.pack(side="left")

        # Set initial active state
        self.set_active("home")

    def _make_nav_button(self, parent, page: str, icon: str, label: str) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text          = f"  {icon}   {label}",
            command       = lambda p=page: self._on_nav_click(p),
            anchor        = "w",
            fg_color      = "transparent",
            hover_color   = Colors.SIDEBAR_HOVER,
            text_color    = Colors.TEXT_SECONDARY,
            corner_radius = 10,
            font          = ("Segoe UI", 13, "normal"),
            height        = 44,
            border_width  = 0,
        )

    # ── public API ────────────────────────────────────────────────────────────
    def set_active(self, page: str):
        """Highlight the active nav item."""
        for p, btn in self._buttons.items():
            if p == page:
                btn.configure(
                    fg_color   = Colors.SIDEBAR_ACTIVE,
                    text_color = Colors.NEON_CYAN,
                    font       = ("Segoe UI", 13, "bold"),
                    border_width  = 1,
                    border_color  = Colors.BORDER_DIM,
                )
            else:
                btn.configure(
                    fg_color     = "transparent",
                    text_color   = Colors.TEXT_SECONDARY,
                    font         = ("Segoe UI", 13, "normal"),
                    border_width = 0,
                )
        self.active_page = page

    def set_status(self, text: str, color: str = Colors.NEON_GREEN):
        """Update the bottom status indicator."""
        self.status_dot.configure(text_color=color)
        self.status_label.configure(text=f" {text}")

    # ── private ───────────────────────────────────────────────────────────────
    def _on_nav_click(self, page: str):
        self.set_active(page)
        self.navigate_callback(page)