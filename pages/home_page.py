"""
ui/pages/home_page.py — Dashboard Home Page
KPI tiles, skill radar, performance chart, weak skills panel,
AI suggestions, and recent activity timeline.
"""

import math
import tkinter as tk
from datetime import datetime
from typing import List, Dict, Callable

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches
import numpy as np

from config import Colors, Fonts, Layout, MATPLOTLIB_STYLE
from database import get_db
from ui.components import (
    GlassCard, MetricTile, CircularGauge,
    NeonButton, Badge, ScrollableCardFrame, SectionHeader, Divider
)
from ui.theme import score_color

# Apply matplotlib dark style
for k, v in MATPLOTLIB_STYLE.items():
    try:
        plt.rcParams[k] = v
    except Exception:
        pass


class HomePage(ctk.CTkFrame):
    def __init__(self, master, navigate_cb: Callable, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._navigate  = navigate_cb
        self._db        = get_db()
        self._stats     = {}
        self.build()
        self.refresh()

    # ─────────────────────────────────────────
    def build(self):
        # Main scrollable container
        self._scroll = ScrollableCardFrame(self)
        self._scroll.pack(fill="both", expand=True, padx=0, pady=0)

        inner = self._scroll
        pad = {"padx": 20, "pady": 0}

        # ── Header ──────────────────────────
        hdr = SectionHeader(
            inner,
            title="Dashboard",
            subtitle="Your career intelligence at a glance",
            action_text="⟳  Refresh",
            action_cmd=self.refresh,
        )
        hdr.pack(fill="x", **pad, pady=(20, 12))

        # ── Row 1: KPI Tiles ─────────────────
        self._kpi_row = ctk.CTkFrame(inner, fg_color="transparent")
        self._kpi_row.pack(fill="x", **pad, pady=(0, 16))

        self._ats_tile  = MetricTile(self._kpi_row, "ATS Score", "—%",
                                      subtitle="Resume compatibility",
                                      icon="📄", accent=Colors.NEON_CYAN)
        self._ready_tile = MetricTile(self._kpi_row, "Readiness", "—%",
                                       subtitle="Overall job readiness",
                                       icon="🎯", accent=Colors.NEON_PURPLE)
        self._count_tile = MetricTile(self._kpi_row, "Interviews", "—",
                                       subtitle="Completed sessions",
                                       icon="🎙", accent=Colors.NEON_BLUE)
        self._avg_tile   = MetricTile(self._kpi_row, "Avg Score", "—%",
                                       subtitle="Interview performance",
                                       icon="⭐", accent=Colors.NEON_GREEN)

        for col, tile in enumerate([self._ats_tile, self._ready_tile,
                                     self._count_tile, self._avg_tile]):
            self._kpi_row.columnconfigure(col, weight=1, uniform="kpi")
            tile.grid(row=0, column=col, sticky="nsew", padx=6)

        # ── Row 2: Charts ────────────────────
        charts_row = ctk.CTkFrame(inner, fg_color="transparent")
        charts_row.pack(fill="x", **pad, pady=(0, 16))
        charts_row.columnconfigure(0, weight=4)
        charts_row.columnconfigure(1, weight=3)

        # Performance trend chart (left)
        perf_card = GlassCard(charts_row, title="Performance Trend",
                               accent=Colors.NEON_CYAN)
        perf_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._perf_frame = perf_card.content_frame()
        self._perf_frame.configure(height=220)

        # Skill radar (right)
        radar_card = GlassCard(charts_row, title="Skill Radar",
                                accent=Colors.NEON_PURPLE)
        radar_card.grid(row=0, column=1, sticky="nsew")
        self._radar_frame = radar_card.content_frame()
        self._radar_frame.configure(height=220)

        # ── Row 3: Weak Skills + AI Suggestions ─
        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", **pad, pady=(0, 16))
        row3.columnconfigure(0, weight=1)
        row3.columnconfigure(1, weight=1)

        # Weak skills
        weak_card = GlassCard(row3, title="Skill Gaps",
                               accent=Colors.NEON_ORANGE)
        weak_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._weak_inner = weak_card.content_frame()

        # AI suggestions
        suggest_card = GlassCard(row3, title="AI Recommendations",
                                  accent=Colors.NEON_PURPLE)
        suggest_card.grid(row=0, column=1, sticky="nsew")
        self._suggest_inner = suggest_card.content_frame()

        # ── Row 4: Recent Activity ────────────
        act_card = GlassCard(inner, title="Recent Activity",
                              accent=Colors.NEON_BLUE)
        act_card.pack(fill="x", **pad, pady=(0, 20))
        self._activity_inner = act_card.content_frame()

    # ─────────────────────────────────────────
    #  DATA REFRESH
    # ─────────────────────────────────────────
    def refresh(self):
        self._stats = self._db.get_dashboard_stats()
        self._update_kpis()
        self._draw_perf_chart()
        self._draw_radar()
        self._update_weak_skills()
        self._update_suggestions()
        self._update_activity()

    def _update_kpis(self):
        s = self._stats
        ats  = s.get("ats_score", 0)
        rdy  = s.get("readiness_score", 0)
        cnt  = s.get("interview_count", 0)
        avg  = s.get("avg_score", 0)

        self._ats_tile.update_value(f"{ats:.0f}%", score_color(ats))
        self._ready_tile.update_value(f"{rdy:.0f}%", score_color(rdy))
        self._count_tile.update_value(str(cnt))
        self._avg_tile.update_value(f"{avg:.0f}%", score_color(avg))

    def _draw_perf_chart(self):
        for w in self._perf_frame.winfo_children():
            w.destroy()

        fig, ax = plt.subplots(figsize=(6, 2.6), facecolor=Colors.BG_CARD)
        ax.set_facecolor(Colors.BG_CARD)

        trend = list(reversed(self._stats.get("score_trend", [])))
        if trend:
            scores = [r.get("avg_score", 0) for r in trend]
            labels = [r.get("created_at", "")[:10] for r in trend]
            x = range(len(scores))

            # Gradient fill under line
            ax.fill_between(x, scores, alpha=0.15, color=Colors.NEON_CYAN)
            ax.plot(x, scores, color=Colors.NEON_CYAN, linewidth=2.5,
                    marker="o", markersize=5, markerfacecolor=Colors.NEON_CYAN,
                    markeredgecolor=Colors.BG_CARD)
            ax.set_xticks(list(x))
            ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
            ax.set_ylim(0, 105)
            ax.set_ylabel("Score %", color=Colors.TEXT_SECONDARY, fontsize=9)
        else:
            ax.text(0.5, 0.5, "No interview data yet\nComplete an interview to see trends",
                    ha="center", va="center", color=Colors.TEXT_MUTED,
                    fontsize=10, transform=ax.transAxes)
            ax.set_xticks([])

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(Colors.BORDER_DIM)
        ax.spines["bottom"].set_color(Colors.BORDER_DIM)
        fig.tight_layout(pad=0.8)

        canvas = FigureCanvasTkAgg(fig, master=self._perf_frame)
        canvas.get_tk_widget().configure(bg=Colors.BG_CARD,
                                          highlightthickness=0)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    def _draw_radar(self):
        for w in self._radar_frame.winfo_children():
            w.destroy()

        skills_found = self._stats.get("skills_found", [])
        # Build radar from found skills (up to 6)
        categories = skills_found[:6] if skills_found else [
            "Python", "SQL", "System Design", "Communication",
            "Algorithms", "Cloud"
        ]
        values = [70, 55, 45, 80, 60, 50][:len(categories)]
        # Pad if needed
        while len(values) < len(categories):
            values.append(50)

        N = len(categories)
        angles = [n / N * 2 * math.pi for n in range(N)]
        angles += angles[:1]
        vals = values + values[:1]

        fig, ax = plt.subplots(figsize=(3.2, 2.6),
                                subplot_kw=dict(polar=True),
                                facecolor=Colors.BG_CARD)
        ax.set_facecolor(Colors.BG_CARD)

        ax.plot(angles, vals, color=Colors.NEON_PURPLE, linewidth=2)
        ax.fill(angles, vals, color=Colors.NEON_PURPLE, alpha=0.2)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(
            [c[:8] for c in categories],
            color=Colors.TEXT_SECONDARY, size=8
        )
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", "100"],
                            color=Colors.TEXT_MUTED, size=7)
        ax.grid(color=Colors.BORDER_DIM, linestyle="--", alpha=0.5)
        ax.spines["polar"].set_color(Colors.BORDER_DIM)
        fig.tight_layout(pad=0.5)

        canvas = FigureCanvasTkAgg(fig, master=self._radar_frame)
        canvas.get_tk_widget().configure(bg=Colors.BG_CARD,
                                          highlightthickness=0)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
        plt.close(fig)

    def _update_weak_skills(self):
        for w in self._weak_inner.winfo_children():
            w.destroy()

        weak = self._stats.get("skills_found", [])
        # Simulate proficiency — real data from analytics
        sample_weak = [
            ("System Design", 35), ("Algorithms", 42),
            ("Docker / K8s", 48), ("Cloud Arch.", 55),
        ] if not weak else [(s, 60) for s in weak[:4]]

        if not sample_weak:
            ctk.CTkLabel(self._weak_inner,
                         text="Upload your resume to detect skill gaps",
                         font=ctk.CTkFont(*Fonts.BODY),
                         text_color=Colors.TEXT_MUTED).pack()
            return

        for skill, pct in sample_weak:
            row = ctk.CTkFrame(self._weak_inner, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=skill,
                         font=ctk.CTkFont(*Fonts.LABEL),
                         text_color=Colors.TEXT_PRIMARY,
                         width=120, anchor="w").pack(side="left")

            track = ctk.CTkFrame(row, fg_color=Colors.BORDER_DIM,
                                  corner_radius=4, height=6)
            track.pack(side="left", fill="x", expand=True, padx=8)
            col = score_color(pct)
            ctk.CTkFrame(track, fg_color=col,
                          corner_radius=4, height=6).place(
                relwidth=pct/100, relheight=1
            )

            ctk.CTkLabel(row, text=f"{pct}%",
                         font=ctk.CTkFont(*Fonts.CAPTION),
                         text_color=score_color(pct),
                         width=32).pack(side="right")

        NeonButton(self._weak_inner, text="Build Roadmap →",
                   command=lambda: self._navigate("roadmap"),
                   variant="outline", accent=Colors.NEON_ORANGE
                   ).pack(pady=(10, 0), anchor="w")

    def _update_suggestions(self):
        for w in self._suggest_inner.winfo_children():
            w.destroy()

        suggestions = [
            ("📄", "Add quantified achievements to resume",    Colors.NEON_CYAN),
            ("🎙", "Practice 2 mock interviews this week",     Colors.NEON_PURPLE),
            ("📚", "Study System Design fundamentals",          Colors.NEON_ORANGE),
            ("🔗", "Update LinkedIn with latest projects",      Colors.NEON_GREEN),
        ]

        for icon, text, col in suggestions:
            row = ctk.CTkFrame(self._suggest_inner,
                               fg_color=Colors.BG_CARD_HOVER,
                               corner_radius=8)
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=icon,
                         font=ctk.CTkFont(size=14),
                         width=28).pack(side="left", padx=(10, 6), pady=8)
            ctk.CTkLabel(row, text=text,
                         font=ctk.CTkFont(*Fonts.LABEL),
                         text_color=Colors.TEXT_PRIMARY,
                         wraplength=260, anchor="w",
                         justify="left").pack(side="left",
                                              fill="x", expand=True,
                                              padx=(0, 10), pady=8)

    def _update_activity(self):
        for w in self._activity_inner.winfo_children():
            w.destroy()

        interviews = self._db.get_recent_interviews(limit=5)
        resume     = self._db.get_latest_resume()

        activities = []
        if resume:
            activities.append({
                "icon":  "📄",
                "title": f"Resume analyzed — ATS: {resume['ats_score']:.0f}%",
                "time":  resume["created_at"][:16],
                "color": Colors.NEON_CYAN,
            })
        for iv in interviews[:4]:
            activities.append({
                "icon":  "🎙",
                "title": f"{iv['mode']} interview — Score: {iv['avg_score']:.0f}%  ({iv['domain']})",
                "time":  iv["created_at"][:16],
                "color": Colors.NEON_PURPLE,
            })

        if not activities:
            ctk.CTkLabel(self._activity_inner,
                         text="No activity yet. Upload a resume or start an interview!",
                         font=ctk.CTkFont(*Fonts.BODY),
                         text_color=Colors.TEXT_MUTED).pack(pady=20)
            return

        for i, act in enumerate(activities):
            row = ctk.CTkFrame(self._activity_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # Timeline dot + line
            tl = tk.Canvas(row, width=20, height=36,
                            bg=Colors.BG_CARD, highlightthickness=0)
            tl.pack(side="left", padx=(0, 10))
            tl.create_oval(6, 10, 14, 18, fill=act["color"], outline="")
            if i < len(activities) - 1:
                tl.create_line(10, 18, 10, 36, fill=Colors.BORDER_DIM, width=1)

            ctk.CTkLabel(row, text=f"{act['icon']}  {act['title']}",
                         font=ctk.CTkFont(*Fonts.LABEL),
                         text_color=Colors.TEXT_PRIMARY,
                         anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(row, text=act["time"],
                         font=ctk.CTkFont(*Fonts.CAPTION),
                         text_color=Colors.TEXT_MUTED).pack(side="right")