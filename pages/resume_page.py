"""
ui/pages/resume_page.py — Resume Analyzer Page
PDF upload, ATS scoring, skill detection, Gemini review, export.
"""

import threading
import tkinter as tk
from tkinter import filedialog
from typing import Dict, List, Optional

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import Colors, Fonts, Layout, MATPLOTLIB_STYLE
from database import get_db
from services import get_gemini, get_resume_service, get_report_service
from ui.components import (
    GlassCard, MetricTile, NeonButton, Badge,
    ScrollableCardFrame, SectionHeader, NeonDropdown,
    CircularGauge, Divider, Toast, LoadingSpinner
)
from ui.theme import score_color

for k, v in MATPLOTLIB_STYLE.items():
    try:
        plt.rcParams[k] = v
    except Exception:
        pass


class ResumePage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._db      = get_db()
        self._gemini  = get_gemini()
        self._resume_svc = get_resume_service()
        self._report_svc = get_report_service()
        self._current_data: Optional[Dict] = None
        self._file_path: Optional[str]     = None

        self._build_layout()
        self._load_last_resume()

    # ─────────────────────────────────────────
    def _build_layout(self):
        # Two-panel layout: upload (left) | results (right)
        self._scroll = ScrollableCardFrame(self)
        self._scroll.pack(fill="both", expand=True)

        inner = self._scroll
        SectionHeader(inner,
                       title="Resume Analyzer",
                       subtitle="Upload your PDF resume for ATS analysis and AI feedback",
                       ).pack(fill="x", padx=20, pady=(20, 16))

        body = ctk.CTkFrame(inner, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)

        self._build_upload_panel(body)
        self._build_results_panel(body)

    def _build_upload_panel(self, parent):
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # Upload card
        upload_card = GlassCard(col, title="Upload Resume", accent=Colors.NEON_CYAN)
        upload_card.pack(fill="x", pady=(0, 16))
        uc = upload_card.content_frame()

        # Drop zone
        self._drop_zone = ctk.CTkFrame(
            uc, fg_color=Colors.BG_INPUT,
            corner_radius=12, border_width=2,
            border_color=Colors.BORDER_GLOW, height=160, cursor="hand2",
        )
        self._drop_zone.pack(fill="x", pady=(0, 12))
        self._drop_zone.pack_propagate(False)
        self._drop_zone.bind("<Button-1>", lambda _: self._browse_file())

        dz_inner = ctk.CTkFrame(self._drop_zone, fg_color="transparent")
        dz_inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(dz_inner, text="📄",
                     font=ctk.CTkFont(size=36)).pack()
        self._drop_label = ctk.CTkLabel(
            dz_inner, text="Click to upload PDF",
            font=ctk.CTkFont(*Fonts.BODY_BOLD),
            text_color=Colors.TEXT_PRIMARY,
        )
        self._drop_label.pack(pady=(4, 2))
        ctk.CTkLabel(dz_inner, text="Supports PDF files only",
                     font=ctk.CTkFont(*Fonts.CAPTION),
                     text_color=Colors.TEXT_MUTED).pack()

        # Target role
        ctk.CTkLabel(uc, text="Target Role",
                     font=ctk.CTkFont(*Fonts.LABEL),
                     text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 4))
        self._role_var = tk.StringVar(value="Software Engineer")
        role_entry = ctk.CTkEntry(
            uc, textvariable=self._role_var,
            placeholder_text="e.g. Senior Python Developer",
            fg_color=Colors.BG_INPUT,
            border_color=Colors.BORDER_GLOW,
            text_color=Colors.TEXT_PRIMARY,
            font=ctk.CTkFont(*Fonts.BODY),
            height=36,
        )
        role_entry.pack(fill="x", pady=(0, 12))

        # Analyze button
        NeonButton(uc, text="Analyze Resume",
                   icon="🔍", command=self._start_analysis,
                   accent=Colors.NEON_CYAN).pack(fill="x", pady=(0, 8))
        NeonButton(uc, text="Gemini AI Review",
                   icon="🤖", command=self._run_gemini_review,
                   accent=Colors.NEON_PURPLE, variant="outline").pack(fill="x")

        # ATS Gauge card
        gauge_card = GlassCard(col, title="ATS Score", accent=Colors.NEON_CYAN)
        gauge_card.pack(fill="x", pady=(0, 16))
        gc = gauge_card.content_frame()

        gauge_row = ctk.CTkFrame(gc, fg_color="transparent")
        gauge_row.pack(fill="x", pady=8)
        self._ats_gauge = CircularGauge(gauge_row, size=130,
                                         label="ATS Score",
                                         accent=Colors.NEON_CYAN)
        self._ats_gauge.pack(side="left", padx=(0, 16))

        breakdown = ctk.CTkFrame(gauge_row, fg_color="transparent")
        breakdown.pack(side="left", fill="both", expand=True)
        self._bd_labels: Dict[str, ctk.CTkLabel] = {}
        for cat, pct in [("Keywords", 0), ("Sections", 0),
                          ("Formatting", 0), ("Length", 0)]:
            r = ctk.CTkFrame(breakdown, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=cat,
                         font=ctk.CTkFont(*Fonts.CAPTION),
                         text_color=Colors.TEXT_SECONDARY,
                         width=70, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(r, text="—",
                               font=ctk.CTkFont(*Fonts.CAPTION),
                               text_color=Colors.TEXT_MUTED)
            lbl.pack(side="right")
            self._bd_labels[cat.lower()] = lbl

        # Export button
        NeonButton(col, text="Export PDF Report",
                   icon="📋", command=self._export_report,
                   accent=Colors.NEON_GREEN, variant="outline").pack(fill="x")

    def _build_results_panel(self, parent):
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.grid(row=0, column=1, sticky="nsew")

        # Skills found
        skills_card = GlassCard(col, title="Detected Skills",
                                  accent=Colors.NEON_GREEN)
        skills_card.pack(fill="x", pady=(0, 16))
        self._skills_frame = skills_card.content_frame()
        self._skills_placeholder = ctk.CTkLabel(
            self._skills_frame,
            text="Upload and analyze a resume to see detected skills",
            font=ctk.CTkFont(*Fonts.BODY),
            text_color=Colors.TEXT_MUTED,
        )
        self._skills_placeholder.pack(pady=20)

        # Missing skills
        missing_card = GlassCard(col, title="Missing / Recommended Skills",
                                   accent=Colors.NEON_ORANGE)
        missing_card.pack(fill="x", pady=(0, 16))
        self._missing_frame = missing_card.content_frame()
        ctk.CTkLabel(self._missing_frame,
                     text="Run analysis to see missing skills",
                     font=ctk.CTkFont(*Fonts.BODY),
                     text_color=Colors.TEXT_MUTED).pack(pady=20)

        # Suggestions
        suggest_card = GlassCard(col, title="Improvement Suggestions",
                                   accent=Colors.NEON_PURPLE)
        suggest_card.pack(fill="x", pady=(0, 16))
        self._suggest_frame = suggest_card.content_frame()
        ctk.CTkLabel(self._suggest_frame,
                     text="Suggestions will appear after analysis",
                     font=ctk.CTkFont(*Fonts.BODY),
                     text_color=Colors.TEXT_MUTED).pack(pady=20)

        # Gemini review
        review_card = GlassCard(col, title="Gemini AI Review",
                                  accent=Colors.NEON_PURPLE)
        review_card.pack(fill="x", pady=(0, 16))
        self._review_box = ctk.CTkTextbox(
            review_card.content_frame(),
            height=140,
            fg_color=Colors.BG_INPUT,
            text_color=Colors.TEXT_SECONDARY,
            font=ctk.CTkFont(*Fonts.BODY),
            border_width=0,
            state="disabled",
        )
        self._review_box.pack(fill="x")
        self._set_review_text("Upload your resume and click 'Gemini AI Review' to get an AI-powered analysis...")

    # ─────────────────────────────────────────
    #  FILE HANDLING
    # ─────────────────────────────────────────
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select Resume PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            self._file_path = path
            fname = path.split("/")[-1].split("\\")[-1]
            self._drop_label.configure(
                text=f"✓ {fname}",
                text_color=Colors.NEON_GREEN,
            )
            self._drop_zone.configure(border_color=Colors.NEON_GREEN)

    # ─────────────────────────────────────────
    #  ANALYSIS
    # ─────────────────────────────────────────
    def _start_analysis(self):
        if not self._file_path:
            Toast(self.winfo_toplevel(),
                  "Please upload a PDF resume first", kind="warning")
            return
        threading.Thread(target=self._run_analysis, daemon=True).start()

    def _run_analysis(self):
        try:
            role = self._role_var.get().strip() or "Software Engineer"
            data = self._resume_svc.full_analysis(self._file_path, role)
            self._current_data = data

            # Save to DB (without Gemini review yet)
            fname = (self._file_path or "").split("/")[-1].split("\\")[-1]
            self._db.save_resume({
                "filename":       fname,
                "file_path":      self._file_path,
                "raw_text":       data["raw_text"],
                "ats_score":      data["ats_score"],
                "skills_found":   data["skills_found"],
                "missing_skills": data["missing_skills"],
                "suggestions":    data["suggestions"],
            })

            self.after(0, self._render_results, data)
        except Exception as e:
            self.after(0, lambda: Toast(
                self.winfo_toplevel(), f"Analysis failed: {e}", kind="error"
            ))

    def _render_results(self, data: Dict):
        # ATS gauge
        self._ats_gauge.set_value(data["ats_score"])

        # Breakdown labels
        bd = data.get("ats_breakdown", {})
        for cat in ["keywords", "sections", "formatting", "length"]:
            val = bd.get(cat, {}).get("score", 0)
            if cat in self._bd_labels:
                self._bd_labels[cat].configure(
                    text=f"{val:.0f}pt",
                    text_color=score_color(val * 2.5),
                )

        # Skills
        for w in self._skills_frame.winfo_children():
            w.destroy()
        skills = data.get("skills_found", [])
        if skills:
            flow = ctk.CTkFrame(self._skills_frame, fg_color="transparent")
            flow.pack(fill="x")
            for s in skills[:25]:
                Badge(flow, text=s.title(),
                      color=Colors.NEON_GREEN).pack(
                    side="left", padx=3, pady=3
                )
        else:
            ctk.CTkLabel(self._skills_frame, text="No skills detected",
                         text_color=Colors.TEXT_MUTED,
                         font=ctk.CTkFont(*Fonts.BODY)).pack(pady=10)

        # Missing skills
        for w in self._missing_frame.winfo_children():
            w.destroy()
        missing = data.get("missing_skills", [])
        if missing:
            flow = ctk.CTkFrame(self._missing_frame, fg_color="transparent")
            flow.pack(fill="x")
            for s in missing[:15]:
                Badge(flow, text=s.title(),
                      color=Colors.NEON_ORANGE).pack(
                    side="left", padx=3, pady=3
                )

        # Suggestions
        for w in self._suggest_frame.winfo_children():
            w.destroy()
        for i, s in enumerate(data.get("suggestions", []), 1):
            row = ctk.CTkFrame(self._suggest_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{i}.",
                         font=ctk.CTkFont(*Fonts.BODY_BOLD),
                         text_color=Colors.NEON_CYAN,
                         width=20).pack(side="left")
            ctk.CTkLabel(row, text=s,
                         font=ctk.CTkFont(*Fonts.BODY),
                         text_color=Colors.TEXT_PRIMARY,
                         wraplength=440, justify="left",
                         anchor="w").pack(side="left", fill="x")

        Toast(self.winfo_toplevel(),
              f"Analysis complete! ATS Score: {data['ats_score']:.0f}%",
              kind="success")

    # ─────────────────────────────────────────
    #  GEMINI REVIEW
    # ─────────────────────────────────────────
    def _run_gemini_review(self):
        if not self._current_data:
            Toast(self.winfo_toplevel(),
                  "Run Resume Analysis first", kind="warning")
            return
        if not self._gemini.is_ready:
            Toast(self.winfo_toplevel(),
                  "Gemini API key not configured — go to Settings", kind="error")
            return
        self._set_review_text("🤖 Gemini is reviewing your resume…")
        threading.Thread(target=self._fetch_gemini_review, daemon=True).start()

    def _fetch_gemini_review(self):
        try:
            role = self._role_var.get() or "Software Engineer"
            result = self._gemini.analyze_resume(
                self._current_data["raw_text"], role
            )
            review = result.get("gemini_review", "Review complete.")
            if self._current_data:
                self._current_data["gemini_review"] = review
            self.after(0, self._set_review_text, review)
        except Exception as e:
            self.after(0, self._set_review_text,
                       f"Gemini review failed: {e}")

    def _set_review_text(self, text: str):
        self._review_box.configure(state="normal")
        self._review_box.delete("1.0", "end")
        self._review_box.insert("1.0", text)
        self._review_box.configure(state="disabled")

    # ─────────────────────────────────────────
    #  EXPORT
    # ─────────────────────────────────────────
    def _export_report(self):
        if not self._current_data:
            Toast(self.winfo_toplevel(),
                  "No analysis data to export. Run analysis first.", kind="warning")
            return
        try:
            user = self._db.get_user()
            path = self._report_svc.generate_resume_report(
                self._current_data,
                user_name=user.get("name", "Candidate"),
            )
            Toast(self.winfo_toplevel(),
                  f"Report saved to reports/ folder", kind="success")
        except Exception as e:
            Toast(self.winfo_toplevel(), f"Export failed: {e}", kind="error")

    # ─────────────────────────────────────────
    def _load_last_resume(self):
        """Pre-populate gauge with last known ATS score."""
        resume = self._db.get_latest_resume()
        if resume:
            self._ats_gauge.set_value(resume.get("ats_score", 0))