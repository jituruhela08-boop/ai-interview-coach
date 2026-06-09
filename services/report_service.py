"""
services/report_service.py — PDF Report Generator using ReportLab
Generates professional ATS and Interview performance reports.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from config import REPORTS_DIR, APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  COLOUR PALETTE  (ReportLab Color objects)
# ─────────────────────────────────────────────
C_BG_DARK   = colors.HexColor("#090B15")
C_BG_CARD   = colors.HexColor("#111428")
C_CYAN      = colors.HexColor("#00D4FF")
C_PURPLE    = colors.HexColor("#8B5CF6")
C_BLUE      = colors.HexColor("#3B82F6")
C_GREEN     = colors.HexColor("#10B981")
C_ORANGE    = colors.HexColor("#F59E0B")
C_RED       = colors.HexColor("#EF4444")
C_TEXT      = colors.HexColor("#E8EEFF")
C_MUTED     = colors.HexColor("#7B8EC8")
C_BORDER    = colors.HexColor("#1E2440")
C_WHITE     = colors.white
C_BLACK     = colors.black


def _make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "ReportTitle",
        fontSize=26, fontName="Helvetica-Bold",
        textColor=C_WHITE, alignment=TA_CENTER,
        spaceAfter=4, leading=32,
    )
    styles["subtitle"] = ParagraphStyle(
        "Subtitle",
        fontSize=12, fontName="Helvetica",
        textColor=C_MUTED, alignment=TA_CENTER,
        spaceAfter=16,
    )
    styles["section"] = ParagraphStyle(
        "Section",
        fontSize=14, fontName="Helvetica-Bold",
        textColor=C_CYAN, spaceBefore=16, spaceAfter=8,
    )
    styles["body"] = ParagraphStyle(
        "Body",
        fontSize=10, fontName="Helvetica",
        textColor=C_TEXT, spaceAfter=6, leading=16,
    )
    styles["bullet"] = ParagraphStyle(
        "Bullet",
        fontSize=10, fontName="Helvetica",
        textColor=C_TEXT, spaceAfter=4, leading=14,
        leftIndent=12, bulletIndent=0,
    )
    styles["metric_label"] = ParagraphStyle(
        "MetricLabel",
        fontSize=9, fontName="Helvetica",
        textColor=C_MUTED, alignment=TA_CENTER,
    )
    styles["metric_value"] = ParagraphStyle(
        "MetricValue",
        fontSize=24, fontName="Helvetica-Bold",
        textColor=C_CYAN, alignment=TA_CENTER, leading=28,
    )
    styles["small"] = ParagraphStyle(
        "Small",
        fontSize=9, fontName="Helvetica",
        textColor=C_MUTED, spaceAfter=4,
    )
    return styles


class ReportService:
    """Generates professional PDF reports for resume analysis and interview performance."""

    def __init__(self):
        self.styles = _make_styles()
        self.reports_dir = REPORTS_DIR

    def _doc(self, filename: str) -> SimpleDocTemplate:
        path = self.reports_dir / filename
        return SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )

    def _header_block(self, story: List, title: str, subtitle: str):
        story.append(Paragraph(title, self.styles["title"]))
        story.append(Paragraph(subtitle, self.styles["subtitle"]))
        story.append(HRFlowable(
            width="100%", thickness=1.5,
            color=C_CYAN, spaceAfter=16
        ))

    def _metric_row(self, story: List, metrics: List[tuple]):
        """Renders a row of (label, value, color) metric cards."""
        n = len(metrics)
        col_w = (A4[0] - 4*cm) / n
        tdata = [[
            Paragraph(str(v), ParagraphStyle(
                "MV", fontSize=20, fontName="Helvetica-Bold",
                textColor=c, alignment=TA_CENTER))
            for _, v, c in metrics
        ], [
            Paragraph(lbl, self.styles["metric_label"])
            for lbl, _, _ in metrics
        ]]
        t = Table(tdata, colWidths=[col_w]*n)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_BG_CARD),
            ("BOX",        (0, 0), (-1, -1), 1, C_BORDER),
            ("INNERGRID",  (0, 0), (-1, -1), 0.5, C_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("ROUNDEDCORNERS", [8]),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # ─────────────────────────────────────────
    #  ATS RESUME REPORT
    # ─────────────────────────────────────────
    def generate_resume_report(self, resume_data: Dict,
                                user_name: str = "Candidate") -> str:
        """Generates ATS Resume Analysis report. Returns file path."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ATS_Report_{ts}.pdf"
        doc = self._doc(filename)
        story = []

        self._header_block(
            story,
            f"ATS Resume Analysis Report",
            f"Prepared for {user_name}  •  {datetime.now().strftime('%B %d, %Y')}  •  {APP_NAME}"
        )

        # KPI row
        ats  = resume_data.get("ats_score", 0)
        ats_c = C_GREEN if ats >= 70 else C_ORANGE if ats >= 50 else C_RED
        sf   = len(resume_data.get("skills_found", []))
        ms   = len(resume_data.get("missing_skills", []))
        self._metric_row(story, [
            ("ATS Score",       f"{ats}%",  ats_c),
            ("Skills Found",    str(sf),    C_CYAN),
            ("Missing Skills",  str(ms),    C_ORANGE),
            ("Suggestions",     str(len(resume_data.get("suggestions", []))), C_PURPLE),
        ])

        # AI Review
        if resume_data.get("gemini_review"):
            story.append(Paragraph("AI Review", self.styles["section"]))
            story.append(Paragraph(resume_data["gemini_review"], self.styles["body"]))

        # Skills Found
        if resume_data.get("skills_found"):
            story.append(Paragraph("Detected Skills", self.styles["section"]))
            skill_text = "  •  ".join(resume_data["skills_found"][:30])
            story.append(Paragraph(skill_text, self.styles["body"]))

        # Missing Skills
        if resume_data.get("missing_skills"):
            story.append(Paragraph("Missing / Recommended Skills", self.styles["section"]))
            for skill in resume_data["missing_skills"][:12]:
                story.append(Paragraph(f"• {skill.title()}", self.styles["bullet"]))

        # Suggestions
        if resume_data.get("suggestions"):
            story.append(Paragraph("Improvement Suggestions", self.styles["section"]))
            for i, s in enumerate(resume_data["suggestions"], 1):
                story.append(Paragraph(f"{i}. {s}", self.styles["bullet"]))

        # Footer
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
        story.append(Paragraph(
            f"Generated by {APP_NAME} v{APP_VERSION}  •  {datetime.now().isoformat()}",
            self.styles["small"]
        ))

        doc.build(story)
        logger.info("ATS report saved: %s", filename)
        return str(self.reports_dir / filename)

    # ─────────────────────────────────────────
    #  INTERVIEW PERFORMANCE REPORT
    # ─────────────────────────────────────────
    def generate_interview_report(self, interview: Dict,
                                   questions: List[Dict],
                                   summary: str = "",
                                   user_name: str = "Candidate") -> str:
        """Generates Interview Performance report. Returns file path."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Interview_Report_{ts}.pdf"
        doc = self._doc(filename)
        story = []

        mode = interview.get("mode", "Interview")
        self._header_block(
            story,
            f"{mode} Interview Performance Report",
            f"{user_name}  •  {interview.get('domain','')}  •  "
            f"{datetime.now().strftime('%B %d, %Y')}  •  {APP_NAME}"
        )

        # KPIs
        avg  = interview.get("avg_score", 0)
        conf = interview.get("confidence_score", 0)
        avg_c = C_GREEN if avg >= 70 else C_ORANGE if avg >= 50 else C_RED
        self._metric_row(story, [
            ("Avg Score",       f"{avg:.0f}%", avg_c),
            ("Confidence",      f"{conf:.0f}%", C_PURPLE),
            ("Questions",       str(interview.get("answered", 0)), C_CYAN),
            ("Difficulty",      interview.get("difficulty", ""), C_BLUE),
        ])

        # AI Summary
        if summary:
            story.append(Paragraph("Performance Summary", self.styles["section"]))
            for para in summary.split("\n\n"):
                if para.strip():
                    story.append(Paragraph(para.strip(), self.styles["body"]))

        # Q&A Breakdown
        if questions:
            story.append(Paragraph("Question-by-Question Breakdown", self.styles["section"]))
            for i, q in enumerate(questions, 1):
                score = q.get("score", 0)
                score_c = C_GREEN if score >= 70 else C_ORANGE if score >= 50 else C_RED

                # Question header row
                q_table = Table([[
                    Paragraph(f"Q{i}: {q['question_text'][:120]}",
                               ParagraphStyle("QT", fontSize=10, fontName="Helvetica-Bold",
                                              textColor=C_CYAN)),
                    Paragraph(f"{score:.0f}/100",
                               ParagraphStyle("QS", fontSize=14, fontName="Helvetica-Bold",
                                              textColor=score_c, alignment=TA_RIGHT)),
                ]], colWidths=["82%", "18%"])
                q_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), C_BG_CARD),
                    ("BOX",        (0, 0), (-1, -1), 0.5, C_BORDER),
                    ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ]))
                story.append(KeepTogether([
                    q_table,
                    Paragraph(
                        q.get("ai_feedback", "")[:300] or "No feedback.",
                        self.styles["small"]
                    ),
                    Spacer(1, 8),
                ]))

        # Footer
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
        story.append(Paragraph(
            f"Generated by {APP_NAME} v{APP_VERSION}  •  {datetime.now().isoformat()}",
            self.styles["small"]
        ))

        doc.build(story)
        logger.info("Interview report saved: %s", filename)
        return str(self.reports_dir / filename)


_report_service: Optional[ReportService] = None

def get_report_service() -> ReportService:
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service