"""
pages/resume_page.py
Resume Analyzer — PDF upload, ATS scoring, keyword analysis, AI feedback.
"""
import threading
import customtkinter as ctk
from config import Colors
from ui.theme import (make_card, make_label, make_neon_button,
                       make_ghost_button, make_textbox, make_progress_bar)
from services.ats_service import compute_ats_score, extract_text_from_pdf
from services.gemini_service import analyze_resume
from services.pdf_generator import generate_resume_report
from utils.helpers import ats_score_label


class ResumePage(ctk.CTkFrame):
    """Resume Analyzer page."""

    def __init__(self, parent, db, sidebar=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db        = db
        self.sidebar   = sidebar
        self._analysis = None
        self._resume_text = ""
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=32, pady=(28, 0))
        ctk.CTkLabel(hdr, text="Resume Analyzer",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 28, "bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="ATS Score · Keyword Gap · AI Feedback",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 12)).pack(side="left", padx=16, pady=8)

        # ── Two-column layout ─────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32, pady=20)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        self._build_upload_panel(body)
        self._build_results_panel(body)

    # ── Upload Panel ──────────────────────────────────────────────────────────
    def _build_upload_panel(self, parent):
        panel = make_card(parent)
        panel.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(panel, text="Upload Resume",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(18, 8))
        ctk.CTkFrame(panel, height=1, fg_color=Colors.BORDER_DIM,
                     corner_radius=0).pack(fill="x", padx=20, pady=(0, 12))

        # Drop zone
        drop_frame = ctk.CTkFrame(panel, fg_color=Colors.BG_INPUT,
                                   corner_radius=12, border_width=1,
                                   border_color=Colors.BORDER_GLOW, height=100)
        drop_frame.pack(fill="x", padx=20, pady=(0, 12))
        drop_frame.pack_propagate(False)

        ctk.CTkLabel(drop_frame, text="◈  Drop PDF here or click Browse",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 12)).pack(expand=True)

        make_neon_button(panel, "Browse PDF File",
                         command=self._browse_pdf).pack(fill="x", padx=20, pady=4)

        # Or paste text
        ctk.CTkLabel(panel, text="— or paste resume text —",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 10)).pack(pady=(8, 2))

        self.text_input = make_textbox(panel, height=200)
        self.text_input.pack(fill="x", padx=20, pady=(2, 8))

        # Job description
        ctk.CTkLabel(panel, text="Job Description (optional)",
                     text_color=Colors.TEXT_SECONDARY,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20)

        self.jd_input = make_textbox(panel, height=80)
        self.jd_input.pack(fill="x", padx=20, pady=(4, 8))

        make_neon_button(panel, "Analyze Resume",
                         command=self._run_analysis).pack(fill="x", padx=20, pady=(4, 16))

        # File name display
        self.file_label = ctk.CTkLabel(panel, text="No file selected",
                                        text_color=Colors.TEXT_MUTED,
                                        font=("Segoe UI", 10))
        self.file_label.pack(pady=(0, 8))

    # ── Results Panel ─────────────────────────────────────────────────────────
    def _build_results_panel(self, parent):
        self.results_frame = make_card(parent)
        self.results_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        self._show_empty_state()

    def _show_empty_state(self):
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.results_frame,
                     text="Upload your resume to see\nyour ATS score and analysis",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 14),
                     justify="center").pack(expand=True)

    def _show_loading(self):
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.results_frame, text="◉  Analyzing…",
                     text_color=Colors.NEON_CYAN,
                     font=("Segoe UI", 16, "bold")).pack(expand=True)
        bar = make_progress_bar(self.results_frame, mode="indeterminate")
        bar.pack(fill="x", padx=40, pady=20)
        bar.start()

    def _show_results(self, local_data: dict, ai_data: dict):
        for w in self.results_frame.winfo_children():
            w.destroy()

        scroll = ctk.CTkScrollableFrame(self.results_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=2, pady=2)

        ats = local_data.get("ats_score", 0)
        label, color = ats_score_label(ats)

        # ── ATS Score hero ────────────────────────────────────────────────────
        hero = ctk.CTkFrame(scroll, fg_color=f"{color}15",
                             corner_radius=12, border_width=1,
                             border_color=f"{color}44")
        hero.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(hero, text=f"{ats:.0f}",
                     text_color=color,
                     font=("Segoe UI", 56, "bold")).pack(pady=(16, 0))
        ctk.CTkLabel(hero, text=f"ATS Score · {label}",
                     text_color=color,
                     font=("Segoe UI", 13, "bold")).pack()
        ctk.CTkLabel(hero, text="out of 100",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 10)).pack(pady=(0, 16))

        # ── Score breakdown ───────────────────────────────────────────────────
        self._section_header(scroll, "Score Breakdown")
        breakdown = [
            ("Keyword Match",     local_data.get("keyword_score", 0),  Colors.NEON_CYAN),
            ("Format / Structure",local_data.get("format_score", 0),   Colors.NEON_PURPLE),
            ("Length",            local_data.get("length_score", 0),   Colors.NEON_BLUE),
            ("JD Match",          local_data.get("jd_match_score", 0), Colors.NEON_GREEN),
        ]
        for name, score, col in breakdown:
            self._score_bar(scroll, name, score, col)

        # ── Checklist ────────────────────────────────────────────────────────
        self._section_header(scroll, "Resume Checklist")
        checks = [
            ("Email address",   local_data.get("has_email", False)),
            ("Phone number",    local_data.get("has_phone", False)),
            ("LinkedIn URL",    local_data.get("has_linkedin", False)),
            ("GitHub URL",      local_data.get("has_github", False)),
            ("Experience section", "experience" in local_data.get("found_sections", [])),
            ("Skills section",    "skills"      in local_data.get("found_sections", [])),
            ("Education section", "education"   in local_data.get("found_sections", [])),
        ]
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=4)
        for i, (name, present) in enumerate(checks):
            icon  = "✓" if present else "✗"
            color = Colors.NEON_GREEN if present else Colors.ERROR
            row   = ctk.CTkFrame(grid, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=icon, text_color=color,
                         font=("Segoe UI", 12, "bold"), width=24).pack(side="left")
            ctk.CTkLabel(row, text=name, text_color=Colors.TEXT_SECONDARY,
                         font=("Segoe UI", 11)).pack(side="left", padx=4)

        # ── Found Skills ──────────────────────────────────────────────────────
        skills = local_data.get("found_keywords", [])
        if skills:
            self._section_header(scroll, f"Found Skills ({len(skills)})")
            tags_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            tags_frame.pack(fill="x", padx=16, pady=4)
            row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            row.pack(fill="x")
            for i, sk in enumerate(skills[:20]):
                if i % 5 == 0 and i > 0:
                    row = ctk.CTkFrame(tags_frame, fg_color="transparent")
                    row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=f"  {sk}  ",
                             fg_color=f"{Colors.NEON_GREEN}22",
                             text_color=Colors.NEON_GREEN,
                             corner_radius=5,
                             font=("Segoe UI", 10, "bold")).pack(side="left", padx=2)

        # ── Missing Skills ────────────────────────────────────────────────────
        missing = local_data.get("missing_keywords", [])
        if missing:
            self._section_header(scroll, f"Missing Keywords ({len(missing)})")
            tags_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            tags_frame.pack(fill="x", padx=16, pady=4)
            row = ctk.CTkFrame(tags_frame, fg_color="transparent")
            row.pack(fill="x")
            for i, mk in enumerate(missing[:15]):
                if i % 5 == 0 and i > 0:
                    row = ctk.CTkFrame(tags_frame, fg_color="transparent")
                    row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=f"  {mk}  ",
                             fg_color=f"{Colors.ERROR}22",
                             text_color=Colors.ERROR,
                             corner_radius=5,
                             font=("Segoe UI", 10)).pack(side="left", padx=2)

        # ── AI Suggestions ────────────────────────────────────────────────────
        sugg = ai_data.get("suggestions", "")
        if sugg:
            self._section_header(scroll, "AI Recommendations")
            ctk.CTkLabel(scroll, text=sugg, text_color=Colors.TEXT_SECONDARY,
                         font=("Segoe UI", 11), wraplength=440,
                         justify="left", anchor="w").pack(fill="x", padx=16, pady=4)

        # ── Actions ───────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=12)
        make_neon_button(btn_row, "Download PDF Report",
                         command=self._download_report,
                         color=Colors.NEON_PURPLE).pack(side="left")
        make_ghost_button(btn_row, "Re-analyze",
                          command=self._run_analysis,
                          color=Colors.NEON_CYAN).pack(side="left", padx=8)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _section_header(self, parent, text):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(hdr, text=text, text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 12, "bold")).pack(side="left")
        ctk.CTkFrame(hdr, height=1, fg_color=Colors.BORDER_DIM,
                     corner_radius=0).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _score_bar(self, parent, label, score, color):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=3)
        ctk.CTkLabel(row, text=label, text_color=Colors.TEXT_SECONDARY,
                     font=("Segoe UI", 11), width=150, anchor="w").pack(side="left")
        bar = ctk.CTkProgressBar(row, height=6, corner_radius=3,
                                  progress_color=color, fg_color=Colors.BORDER_DIM,
                                  width=160)
        bar.set(score / 100)
        bar.pack(side="left", padx=8)
        ctk.CTkLabel(row, text=f"{score:.0f}%", text_color=color,
                     font=("Segoe UI", 11, "bold"), width=40).pack(side="left")

    # ── actions ───────────────────────────────────────────────────────────────
    def _browse_pdf(self):
        try:
            import tkinter.filedialog as fd
            path = fd.askopenfilename(filetypes=[("PDF files", "*.pdf")])
            if path:
                self._resume_text = extract_text_from_pdf(path)
                self.text_input.delete("1.0", "end")
                self.text_input.insert("1.0", self._resume_text[:2000])
                self.file_label.configure(
                    text=path.split("/")[-1].split("\\")[-1],
                    text_color=Colors.NEON_GREEN
                )
        except Exception as e:
            self.file_label.configure(text=f"Error: {e}", text_color=Colors.ERROR)

    def _run_analysis(self):
        text = self.text_input.get("1.0", "end").strip()
        if not text:
            self.file_label.configure(text="Please upload a PDF or paste resume text",
                                       text_color=Colors.WARNING)
            return
        jd = self.jd_input.get("1.0", "end").strip()
        self._resume_text = text
        self._show_loading()
        if self.sidebar:
            self.sidebar.set_status("Analyzing…", Colors.NEON_ORANGE)

        def worker():
            local  = compute_ats_score(text, jd)
            ai     = analyze_resume(text, jd)
            merged = {**local, **{k: v for k, v in ai.items() if k not in local}}
            self._analysis = merged
            self.db.save_resume_analysis(
                filename      = "pasted_resume",
                ats_score     = merged.get("ats_score", 0),
                skills_found  = merged.get("found_keywords", []),
                missing_skills= merged.get("missing_keywords", []),
                suggestions   = merged.get("suggestions", ""),
                full_text     = text[:500],
            )
            self.after(0, lambda: self._show_results(local, ai))
            self.after(0, lambda: self.sidebar.set_status("Ready") if self.sidebar else None)

        threading.Thread(target=worker, daemon=True).start()

    def _download_report(self):
        if not self._analysis:
            return
        from services.pdf_generator import generate_resume_report
        path = generate_resume_report(self._analysis)
        if path:
            self.file_label.configure(text=f"Saved: {path.split('/')[-1]}", text_color=Colors.NEON_GREEN)

    def refresh(self):
        pass