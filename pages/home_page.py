"""
pages/home_page.py
Dashboard home page — KPI cards, recent activity, quick launch.
"""
import customtkinter as ctk
from config import Colors
from ui.theme import make_card, make_label, make_neon_button, make_ghost_button
from utils.helpers import relative_time, score_to_grade


class HomePage(ctk.CTkFrame):
    """Main dashboard overview page."""

    def __init__(self, parent, navigate_callback, db, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.navigate = navigate_callback
        self.db       = db
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 0))

        ctk.CTkLabel(
            header, text="Dashboard",
            text_color = Colors.TEXT_PRIMARY,
            font       = ("Segoe UI", 28, "bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Welcome back · Track your progress",
            text_color = Colors.TEXT_MUTED,
            font       = ("Segoe UI", 12),
        ).pack(side="left", padx=(16, 0), pady=(8, 0))

        # ── KPI Cards row ─────────────────────────────────────────────────────
        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", padx=32, pady=(20, 0))

        stats = self.db.get_session_stats()
        total     = stats.get("total", 0)
        avg_score = stats.get("avg_score") or 0.0
        best      = stats.get("best_score") or 0.0
        mins      = stats.get("total_time") or 0

        resumes = self.db.get_resume_analyses(limit=1)
        ats_score = resumes[0].get("ats_score", 0) if resumes else 0

        kpi_data = [
            ("Interviews", str(total),               Colors.NEON_CYAN,   "◉  Total Sessions"),
            ("Avg Score",  f"{avg_score:.1f}/10",    Colors.NEON_PURPLE, "◎  Average Score"),
            ("Best Score", f"{best:.1f}/10",          Colors.NEON_GREEN,  "◆  Personal Best"),
            ("ATS Score",  f"{ats_score:.0f}%",       Colors.NEON_ORANGE, "◈  Last Resume"),
        ]

        for col, (title, value, color, subtitle) in enumerate(kpi_data):
            kpi_row.columnconfigure(col, weight=1)
            card = self._make_kpi_card(kpi_row, title, value, color, subtitle)
            card.grid(row=0, column=col, padx=8, sticky="nsew")

        # ── Content row ───────────────────────────────────────────────────────
        content_row = ctk.CTkFrame(self, fg_color="transparent")
        content_row.pack(fill="both", expand=True, padx=32, pady=20)
        content_row.columnconfigure(0, weight=3)
        content_row.columnconfigure(1, weight=2)
        content_row.rowconfigure(0, weight=1)

        # Left — recent sessions
        self._build_recent_sessions(content_row)

        # Right — quick actions + tips
        self._build_quick_actions(content_row)

    def _make_kpi_card(self, parent, title, value, color, subtitle):
        card = make_card(parent, border_color=f"{color}33")
        card.configure(height=120)
        card.pack_propagate(False)

        ctk.CTkLabel(
            card, text=subtitle,
            text_color = Colors.TEXT_MUTED,
            font       = ("Segoe UI", 10),
            anchor     = "w",
        ).pack(anchor="w", padx=18, pady=(16, 2))

        ctk.CTkLabel(
            card, text=value,
            text_color = color,
            font       = ("Segoe UI", 28, "bold"),
            anchor     = "w",
        ).pack(anchor="w", padx=18, pady=0)

        ctk.CTkLabel(
            card, text=title,
            text_color = Colors.TEXT_SECONDARY,
            font       = ("Segoe UI", 11),
            anchor     = "w",
        ).pack(anchor="w", padx=18, pady=(2, 16))

        # Coloured bottom accent
        ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0).pack(
            fill="x", side="bottom"
        )
        return card

    def _build_recent_sessions(self, parent):
        card = make_card(parent)
        card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(18, 0))
        ctk.CTkLabel(hdr, text="Recent Sessions",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 14, "bold")).pack(side="left")
        make_ghost_button(hdr, "View All",
                          command=lambda: self.navigate("analytics"),
                          color=Colors.NEON_CYAN, height=28,
                          font=("Segoe UI", 11)).pack(side="right")

        ctk.CTkFrame(card, height=1, fg_color=Colors.BORDER_DIM, corner_radius=0).pack(fill="x", padx=20, pady=8)

        sessions = self.db.get_sessions(limit=6)

        if not sessions:
            empty = ctk.CTkFrame(card, fg_color="transparent")
            empty.pack(fill="both", expand=True)
            ctk.CTkLabel(
                empty, text="◉  No sessions yet",
                text_color = Colors.TEXT_MUTED,
                font       = ("Segoe UI", 13),
            ).pack(expand=True)
            make_neon_button(
                empty, "Start Your First Interview",
                command = lambda: self.navigate("interview"),
            ).pack(pady=(0, 24))
            return

        for s in sessions:
            self._make_session_row(card, s)

    def _make_session_row(self, parent, session):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=3)

        # Domain badge
        ctk.CTkLabel(
            row, text=f"  {session.get('domain','?')[:12]}  ",
            fg_color   = f"{Colors.NEON_PURPLE}22",
            text_color = Colors.NEON_PURPLE,
            corner_radius = 6,
            font       = ("Segoe UI", 10, "bold"),
        ).pack(side="left")

        # Mode
        ctk.CTkLabel(
            row, text=f"  {session.get('mode','')[:8]}  ",
            fg_color   = f"{Colors.NEON_BLUE}22",
            text_color = Colors.NEON_BLUE,
            corner_radius = 6,
            font       = ("Segoe UI", 10),
        ).pack(side="left", padx=6)

        # Time
        ctk.CTkLabel(
            row, text=relative_time(session.get("created_at", "")),
            text_color = Colors.TEXT_MUTED,
            font       = ("Segoe UI", 10),
        ).pack(side="left", padx=4)

        # Score
        score = session.get("score", 0) or 0
        grade, col = score_to_grade(score)
        ctk.CTkLabel(
            row, text=f"{score:.1f}  {grade}",
            text_color = col,
            font       = ("Segoe UI", 12, "bold"),
        ).pack(side="right")

    def _build_quick_actions(self, parent):
        card = make_card(parent)
        card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        ctk.CTkLabel(card, text="Quick Actions",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(18, 8))

        ctk.CTkFrame(card, height=1, fg_color=Colors.BORDER_DIM, corner_radius=0).pack(fill="x", padx=20, pady=(0, 12))

        actions = [
            ("◉  Start Mock Interview",  Colors.NEON_CYAN,   "interview"),
            ("◈  Analyze Resume",        Colors.NEON_PURPLE, "resume"),
            ("◆  Generate Roadmap",      Colors.NEON_GREEN,  "roadmap"),
            ("◎  View Analytics",        Colors.NEON_BLUE,   "analytics"),
        ]

        for label, color, page in actions:
            ctk.CTkButton(
                card, text=label,
                command      = lambda p=page: self.navigate(p),
                anchor       = "w",
                fg_color     = f"{color}15",
                hover_color  = f"{color}25",
                text_color   = color,
                border_width = 1,
                border_color = f"{color}44",
                corner_radius= 10,
                font         = ("Segoe UI", 12, "bold"),
                height       = 46,
            ).pack(fill="x", padx=20, pady=4)

        # Tips card
        ctk.CTkLabel(card, text="💡  Pro Tips",
                     text_color=Colors.TEXT_SECONDARY,
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(16, 4))

        tips = [
            "Upload your resume before interviews for targeted questions",
            "Practice the same domain 3× to see score improvement",
            "Review AI feedback carefully — it shows your weak spots",
        ]
        for tip in tips:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text="·", text_color=Colors.NEON_CYAN,
                         font=("Segoe UI", 14, "bold")).pack(side="left")
            ctk.CTkLabel(row, text=f"  {tip}", text_color=Colors.TEXT_MUTED,
                         font=("Segoe UI", 10), anchor="w",
                         wraplength=220, justify="left").pack(side="left")

    def refresh(self):
        """Reload all widgets from DB."""
        for w in self.winfo_children():
            w.destroy()
        self._build()