"""
pages/interview_page.py
Mock Interview System — Technical, HR, Mixed modes with Gemini AI evaluation.
"""
import threading
import time
import customtkinter as ctk
from config import Colors, INTERVIEW_MODES, DIFFICULTY_LEVELS, TECH_DOMAINS
from ui.theme import (make_card, make_neon_button, make_ghost_button,
                       make_dropdown, make_textbox, make_progress_bar)
from services.gemini_service import generate_interview_question, evaluate_answer
from utils.helpers import format_duration, score_to_grade


class InterviewPage(ctk.CTkFrame):
    """Mock Interview page with setup, active interview, and results views."""

    def __init__(self, parent, db, sidebar=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db              = db
        self.sidebar         = sidebar
        # State
        self._session        = None
        self._questions      = []
        self._answers        = []
        self._feedbacks      = []
        self._scores         = []
        self._current_q      = 0
        self._start_time     = 0
        self._timer_running  = False
        self._timer_label    = None
        self._num_questions  = 5
        self._build_setup_view()

    # ══════════════════════════════════════════════════════════════════════════
    # SETUP VIEW
    # ══════════════════════════════════════════════════════════════════════════
    def _build_setup_view(self):
        self._clear()

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=32, pady=(28, 0))
        ctk.CTkLabel(hdr, text="Mock Interview",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 28, "bold")).pack(side="left")
        ctk.CTkLabel(hdr, text="AI-Powered · Real-time Feedback",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 12)).pack(side="left", padx=16, pady=8)

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32, pady=20)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_config_card(body)
        self._build_info_card(body)

    def _build_config_card(self, parent):
        card = make_card(parent, border_color=f"{Colors.NEON_CYAN}44")
        card.grid(row=0, column=0, padx=(0, 12), sticky="nsew")

        ctk.CTkLabel(card, text="Interview Setup",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(card, text="Configure your session below",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 11)).pack(anchor="w", padx=24, pady=(0, 12))
        ctk.CTkFrame(card, height=1, fg_color=Colors.BORDER_DIM, corner_radius=0).pack(fill="x", padx=24, pady=(0, 16))

        def field(label, widget_fn):
            ctk.CTkLabel(card, text=label, text_color=Colors.TEXT_SECONDARY,
                         font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=24, pady=(8, 2))
            w = widget_fn()
            w.pack(fill="x", padx=24, pady=(0, 4))
            return w

        self.mode_var  = ctk.StringVar(value=INTERVIEW_MODES[0])
        self.mode_dd   = field("Interview Mode",
            lambda: make_dropdown(card, INTERVIEW_MODES, variable=self.mode_var))

        self.domain_var = ctk.StringVar(value=TECH_DOMAINS[0])
        self.domain_dd  = field("Domain / Topic",
            lambda: make_dropdown(card, TECH_DOMAINS, variable=self.domain_var))

        self.diff_var  = ctk.StringVar(value=DIFFICULTY_LEVELS[1])
        self.diff_dd   = field("Difficulty",
            lambda: make_dropdown(card, DIFFICULTY_LEVELS, variable=self.diff_var))

        # Question count slider
        ctk.CTkLabel(card, text="Number of Questions",
                     text_color=Colors.TEXT_SECONDARY,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=24, pady=(8, 2))
        self.q_count_var = ctk.IntVar(value=5)
        slider_row = ctk.CTkFrame(card, fg_color="transparent")
        slider_row.pack(fill="x", padx=24)

        self.q_slider = ctk.CTkSlider(slider_row, from_=3, to=15,
                                       variable=self.q_count_var,
                                       progress_color=Colors.NEON_CYAN,
                                       fg_color=Colors.BORDER_DIM,
                                       button_color=Colors.NEON_CYAN,
                                       command=self._update_q_label)
        self.q_slider.pack(side="left", fill="x", expand=True)
        self.q_count_label = ctk.CTkLabel(slider_row, text="5",
                                           text_color=Colors.NEON_CYAN,
                                           font=("Segoe UI", 12, "bold"), width=30)
        self.q_count_label.pack(side="left", padx=(8, 0))

        ctk.CTkFrame(card, fg_color="transparent", height=16).pack()

        make_neon_button(card, "▶  Start Interview",
                         command=self._start_interview,
                         height=48, font=("Segoe UI", 14, "bold")).pack(
                             fill="x", padx=24, pady=(8, 24))

    def _update_q_label(self, val):
        n = int(float(val))
        self._num_questions = n
        self.q_count_label.configure(text=str(n))

    def _build_info_card(self, parent):
        card = make_card(parent)
        card.grid(row=0, column=1, padx=(12, 0), sticky="nsew")

        ctk.CTkLabel(card, text="How It Works",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=24, pady=(20, 12))

        steps = [
            ("01", Colors.NEON_CYAN,   "Configure",  "Choose domain, mode, difficulty and question count"),
            ("02", Colors.NEON_PURPLE, "Answer",     "Type your answers at your own pace"),
            ("03", Colors.NEON_GREEN,  "AI Feedback","Gemini evaluates each answer with a score and tips"),
            ("04", Colors.NEON_ORANGE, "Report",     "Download a PDF report of your full session"),
        ]
        for num, col, title, desc in steps:
            row = ctk.CTkFrame(card, fg_color=f"{col}10",
                                corner_radius=10, border_width=1,
                                border_color=f"{col}33")
            row.pack(fill="x", padx=24, pady=6)
            ctk.CTkLabel(row, text=num, text_color=col,
                         font=("Segoe UI", 20, "bold"), width=40).pack(side="left", padx=12, pady=12)
            col_frame = ctk.CTkFrame(row, fg_color="transparent")
            col_frame.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(col_frame, text=title, text_color=Colors.TEXT_PRIMARY,
                         font=("Segoe UI", 12, "bold"), anchor="w").pack(anchor="w", pady=(8, 0))
            ctk.CTkLabel(col_frame, text=desc, text_color=Colors.TEXT_MUTED,
                         font=("Segoe UI", 10), anchor="w",
                         wraplength=280).pack(anchor="w", pady=(0, 8))

        # Previous session count
        stats = self.db.get_session_stats()
        total = stats.get("total", 0)
        ctk.CTkFrame(card, height=1, fg_color=Colors.BORDER_DIM, corner_radius=0).pack(fill="x", padx=24, pady=(16, 8))
        ctk.CTkLabel(card, text=f"◉  {total} sessions completed",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 11)).pack(anchor="w", padx=24, pady=(0, 16))

    # ══════════════════════════════════════════════════════════════════════════
    # ACTIVE INTERVIEW VIEW
    # ══════════════════════════════════════════════════════════════════════════
    def _start_interview(self):
        self._num_questions = int(self.q_count_var.get())
        self._questions = []
        self._answers   = []
        self._feedbacks = []
        self._scores    = []
        self._current_q = 0
        self._start_time = time.time()
        self._session = {
            "mode":       self.mode_var.get(),
            "domain":     self.domain_var.get(),
            "difficulty": self.diff_var.get(),
        }
        self._clear()
        self._build_interview_view()
        self._load_next_question()

    def _build_interview_view(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color=Colors.BG_CARD,
                            corner_radius=0, border_width=0, height=64)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkLabel(top, text=f"◉  {self._session['domain']} · {self._session['mode']}",
                     text_color=Colors.NEON_CYAN,
                     font=("Segoe UI", 13, "bold")).pack(side="left", padx=24, pady=20)

        # Progress
        self.progress_label = ctk.CTkLabel(top,
            text=f"Q 1 / {self._num_questions}",
            text_color=Colors.TEXT_SECONDARY,
            font=("Segoe UI", 12))
        self.progress_label.pack(side="left", padx=12)

        # Timer
        self._timer_label = ctk.CTkLabel(top, text="00:00",
                                          text_color=Colors.NEON_ORANGE,
                                          font=("Segoe UI", 14, "bold"))
        self._timer_label.pack(side="right", padx=24)

        make_ghost_button(top, "End Session",
                          command=self._end_session_early,
                          color=Colors.ERROR, height=32).pack(side="right", padx=8)

        # Progress bar
        self.prog_bar = ctk.CTkProgressBar(self, progress_color=Colors.NEON_CYAN,
                                            fg_color=Colors.BORDER_DIM,
                                            corner_radius=0, height=3)
        self.prog_bar.pack(fill="x")
        self.prog_bar.set(0)

        # Main body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=40, pady=24)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Question panel
        q_card = make_card(body, border_color=f"{Colors.NEON_CYAN}44")
        q_card.grid(row=0, column=0, padx=(0, 12), sticky="nsew")

        q_top = ctk.CTkFrame(q_card, fg_color="transparent")
        q_top.pack(fill="x", padx=20, pady=(18, 0))
        self.q_num_label = ctk.CTkLabel(q_top, text="Question 1",
                                         text_color=Colors.NEON_CYAN,
                                         font=("Segoe UI", 12, "bold"))
        self.q_num_label.pack(side="left")
        ctk.CTkLabel(q_top, text=f"  ·  {self._session['difficulty']}",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 11)).pack(side="left")

        ctk.CTkFrame(q_card, height=1, fg_color=Colors.BORDER_DIM, corner_radius=0).pack(fill="x", padx=20, pady=8)

        # Question text
        self.q_text = ctk.CTkLabel(q_card, text="Loading question…",
                                    text_color=Colors.TEXT_PRIMARY,
                                    font=("Segoe UI", 13),
                                    wraplength=480, justify="left", anchor="w")
        self.q_text.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        # Answer area
        ctk.CTkLabel(q_card, text="Your Answer",
                     text_color=Colors.TEXT_SECONDARY,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20)
        self.answer_box = make_textbox(q_card, height=200)
        self.answer_box.pack(fill="x", padx=20, pady=(4, 12))

        btn_row = ctk.CTkFrame(q_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))
        self.submit_btn = make_neon_button(btn_row, "Submit Answer",
                                            command=self._submit_answer)
        self.submit_btn.pack(side="left")
        make_ghost_button(btn_row, "Skip",
                          command=self._skip_question,
                          color=Colors.TEXT_MUTED, height=36).pack(side="left", padx=8)

        # Feedback panel
        self.feedback_card = make_card(body)
        self.feedback_card.grid(row=0, column=1, padx=(12, 0), sticky="nsew")

        ctk.CTkLabel(self.feedback_card, text="AI Feedback",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(18, 8))
        ctk.CTkFrame(self.feedback_card, height=1, fg_color=Colors.BORDER_DIM,
                     corner_radius=0).pack(fill="x", padx=20, pady=(0, 8))

        self.feedback_scroll = ctk.CTkScrollableFrame(self.feedback_card, fg_color="transparent")
        self.feedback_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 16))

        ctk.CTkLabel(self.feedback_scroll,
                     text="Submit an answer to\nreceive AI feedback",
                     text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 12), justify="center").pack(expand=True, pady=40)

        # Start timer
        self._timer_running = True
        self._tick_timer()

    def _tick_timer(self):
        if self._timer_running and self._timer_label:
            elapsed = int(time.time() - self._start_time)
            self._timer_label.configure(text=format_duration(elapsed))
            self.after(1000, self._tick_timer)

    def _load_next_question(self):
        if self._current_q >= self._num_questions:
            self._end_session()
            return

        self.q_num_label.configure(text=f"Question {self._current_q + 1}")
        self.progress_label.configure(text=f"Q {self._current_q + 1} / {self._num_questions}")
        self.prog_bar.set(self._current_q / self._num_questions)
        self.q_text.configure(text="Generating question…", text_color=Colors.TEXT_MUTED)
        self.answer_box.delete("1.0", "end")
        self.submit_btn.configure(state="disabled")

        # Clear feedback
        for w in self.feedback_scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.feedback_scroll, text="Answer the question →",
                     text_color=Colors.TEXT_MUTED, font=("Segoe UI", 12)).pack(pady=40)

        def gen():
            q = generate_interview_question(
                self._session["domain"],
                self._session["difficulty"],
                self._session["mode"],
                self._questions,
            )
            self.after(0, lambda: self._on_question_ready(q))

        threading.Thread(target=gen, daemon=True).start()

    def _on_question_ready(self, question: str):
        self._current_q_text = question
        self.q_text.configure(text=question, text_color=Colors.TEXT_PRIMARY)
        self.submit_btn.configure(state="normal")

    def _submit_answer(self):
        answer = self.answer_box.get("1.0", "end").strip()
        if not answer:
            return
        self._questions.append(self._current_q_text)
        self._answers.append(answer)
        self.submit_btn.configure(state="disabled", text="Evaluating…")

        for w in self.feedback_scroll.winfo_children():
            w.destroy()
        bar = ctk.CTkProgressBar(self.feedback_scroll, mode="indeterminate",
                                  progress_color=Colors.NEON_CYAN)
        bar.pack(fill="x", padx=12, pady=20)
        bar.start()

        def eval_worker():
            fb = evaluate_answer(
                self._current_q_text, answer,
                self._session["domain"], self._session["difficulty"]
            )
            self._feedbacks.append(fb)
            # Parse score from feedback
            import re
            m = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", fb)
            score = float(m.group(1)) if m else 6.0
            self._scores.append(score)
            self.after(0, lambda: self._show_feedback(fb, score))

        threading.Thread(target=eval_worker, daemon=True).start()

    def _show_feedback(self, feedback: str, score: float):
        for w in self.feedback_scroll.winfo_children():
            w.destroy()

        grade, col = score_to_grade(score)
        score_frame = ctk.CTkFrame(self.feedback_scroll,
                                    fg_color=f"{col}15",
                                    corner_radius=10, border_width=1,
                                    border_color=f"{col}44")
        score_frame.pack(fill="x", padx=8, pady=(8, 12))
        ctk.CTkLabel(score_frame, text=f"{score:.0f}/10  {grade}",
                     text_color=col, font=("Segoe UI", 18, "bold")).pack(pady=12)

        ctk.CTkLabel(self.feedback_scroll, text=feedback,
                     text_color=Colors.TEXT_SECONDARY,
                     font=("Segoe UI", 11), wraplength=340,
                     justify="left", anchor="w").pack(fill="x", padx=8, pady=4)

        # Next button
        n = self._num_questions
        i = self._current_q + 1
        btn_text = f"Next Question ({i}/{n})" if i < n else "Finish Interview"
        make_neon_button(self.feedback_scroll, btn_text,
                          command=self._next_question).pack(fill="x", padx=8, pady=12)
        self.submit_btn.configure(state="normal", text="Submit Answer")

    def _next_question(self):
        self._current_q += 1
        self._load_next_question()

    def _skip_question(self):
        self._questions.append(self._current_q_text)
        self._answers.append("[Skipped]")
        self._feedbacks.append("")
        self._scores.append(0)
        self._current_q += 1
        self._load_next_question()

    def _end_session_early(self):
        self._timer_running = False
        self._save_and_show_results()

    def _end_session(self):
        self._timer_running = False
        self._save_and_show_results()

    # ══════════════════════════════════════════════════════════════════════════
    # RESULTS VIEW
    # ══════════════════════════════════════════════════════════════════════════
    def _save_and_show_results(self):
        duration = int((time.time() - self._start_time) / 60)
        avg = sum(self._scores) / len(self._scores) if self._scores else 0

        self.db.save_session(
            mode       = self._session["mode"],
            domain     = self._session["domain"],
            difficulty = self._session["difficulty"],
            score      = round(avg, 2),
            duration   = duration,
            questions  = self._questions,
            answers    = self._answers,
            feedback   = "; ".join(self._feedbacks),
        )
        self._session["score"]    = round(avg, 2)
        self._session["duration"] = duration
        self._clear()
        self._build_results_view(avg, duration)

    def _build_results_view(self, avg_score: float, duration: int):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=32, pady=(28, 0))
        ctk.CTkLabel(hdr, text="Session Complete",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 28, "bold")).pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32, pady=20)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # Left — score summary
        grade, col = score_to_grade(avg_score)
        summary = make_card(body, border_color=f"{col}44")
        summary.grid(row=0, column=0, padx=(0, 12), sticky="nsew")

        ctk.CTkLabel(summary, text=f"{avg_score:.1f}",
                     text_color=col, font=("Segoe UI", 72, "bold")).pack(pady=(28, 0))
        ctk.CTkLabel(summary, text=f"Overall Score  ·  {grade}",
                     text_color=col, font=("Segoe UI", 14, "bold")).pack()
        ctk.CTkLabel(summary, text="out of 10.0",
                     text_color=Colors.TEXT_MUTED, font=("Segoe UI", 11)).pack(pady=(0, 16))
        ctk.CTkFrame(summary, height=1, fg_color=Colors.BORDER_DIM, corner_radius=0).pack(fill="x", padx=20, pady=8)

        meta = [
            ("Domain",     self._session.get("domain", "")),
            ("Mode",       self._session.get("mode", "")),
            ("Difficulty", self._session.get("difficulty", "")),
            ("Questions",  str(len(self._questions))),
            ("Duration",   f"{duration} min"),
        ]
        for k, v in meta:
            row = ctk.CTkFrame(summary, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=2)
            ctk.CTkLabel(row, text=k, text_color=Colors.TEXT_MUTED,
                         font=("Segoe UI", 11), width=90, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=v, text_color=Colors.TEXT_PRIMARY,
                         font=("Segoe UI", 11, "bold")).pack(side="left")

        # Per-question scores bar chart
        if self._scores:
            ctk.CTkLabel(summary, text="Per-Question Scores",
                         text_color=Colors.TEXT_SECONDARY,
                         font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=24, pady=(16, 4))
            for i, s in enumerate(self._scores):
                row = ctk.CTkFrame(summary, fg_color="transparent")
                row.pack(fill="x", padx=24, pady=2)
                _, c = score_to_grade(s)
                ctk.CTkLabel(row, text=f"Q{i+1}", text_color=Colors.TEXT_MUTED,
                             font=("Segoe UI", 10), width=24).pack(side="left")
                bar = ctk.CTkProgressBar(row, height=6, corner_radius=3,
                                          progress_color=c,
                                          fg_color=Colors.BORDER_DIM, width=120)
                bar.set(s / 10)
                bar.pack(side="left", padx=6)
                ctk.CTkLabel(row, text=f"{s:.1f}", text_color=c,
                             font=("Segoe UI", 10, "bold"), width=28).pack(side="left")

        # Action buttons
        btn_row = ctk.CTkFrame(summary, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(16, 24))
        make_neon_button(btn_row, "New Interview",
                          command=self._build_setup_view).pack(fill="x", pady=4)
        make_ghost_button(btn_row, "Download Report",
                          command=self._download_session_report,
                          color=Colors.NEON_PURPLE).pack(fill="x", pady=4)

        # Right — Q&A review
        qa_card = make_card(body)
        qa_card.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
        ctk.CTkLabel(qa_card, text="Answer Review",
                     text_color=Colors.TEXT_PRIMARY,
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(18, 8))
        ctk.CTkFrame(qa_card, height=1, fg_color=Colors.BORDER_DIM,
                     corner_radius=0).pack(fill="x", padx=20, pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(qa_card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 16))

        for i, (q, a, fb, s) in enumerate(zip(
                self._questions, self._answers, self._feedbacks, self._scores)):
            _, c = score_to_grade(s)
            qcard = ctk.CTkFrame(scroll, fg_color=Colors.BG_CARD,
                                  corner_radius=10, border_width=1,
                                  border_color=f"{c}33")
            qcard.pack(fill="x", padx=8, pady=6)

            top_row = ctk.CTkFrame(qcard, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(10, 4))
            ctk.CTkLabel(top_row, text=f"Q{i+1}",
                         text_color=Colors.NEON_CYAN, font=("Segoe UI", 11, "bold")).pack(side="left")
            ctk.CTkLabel(top_row, text=f"Score: {s:.1f}/10  {score_to_grade(s)[0]}",
                         text_color=c, font=("Segoe UI", 11, "bold")).pack(side="right")

            ctk.CTkLabel(qcard, text=q, text_color=Colors.TEXT_PRIMARY,
                         font=("Segoe UI", 11), wraplength=400,
                         justify="left", anchor="w").pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(qcard, text=f"Your answer: {a[:200]}",
                         text_color=Colors.TEXT_MUTED, font=("Segoe UI", 10),
                         wraplength=400, justify="left", anchor="w").pack(fill="x", padx=12, pady=(0, 8))

    def _download_session_report(self):
        from services.pdf_generator import generate_interview_report
        path = generate_interview_report({
            "created_at":    "",
            "mode":          self._session.get("mode", ""),
            "domain":        self._session.get("domain", ""),
            "difficulty":    self._session.get("difficulty", ""),
            "score":         self._session.get("score", 0),
            "duration":      self._session.get("duration", 0),
            "questions":     self._questions,
            "answers":       self._answers,
            "feedback_list": self._feedbacks,
        })
        if path and self.sidebar:
            self.sidebar.set_status(f"Report saved", Colors.NEON_GREEN)

    # ── utils ─────────────────────────────────────────────────────────────────
    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def refresh(self):
        pass