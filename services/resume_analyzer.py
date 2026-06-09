"""
services/resume_service.py — PDF Resume Parser & ATS Scorer
Handles PDF extraction, local ATS keyword analysis, and skill detection.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import PyPDF2

from config import ATS_KEYWORDS, SKILL_CATEGORIES

logger = logging.getLogger(__name__)


class ResumeService:
    """Parses PDF resumes, scores ATS compatibility, detects skills."""

    # Common section headers for structural analysis
    SECTION_HEADERS = [
        "experience", "education", "skills", "projects", "certifications",
        "achievements", "summary", "objective", "publications", "awards",
        "languages", "interests", "references", "work history", "employment"
    ]

    def extract_text(self, file_path: str) -> str:
        """Extract all text from a PDF file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported.")
        text_parts = []
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages):
                    try:
                        text_parts.append(page.extract_text() or "")
                    except Exception as e:
                        logger.warning("Page %d extraction failed: %s", page_num, e)
        except Exception as e:
            logger.error("PDF read failed: %s", e)
            raise RuntimeError(f"Could not read PDF: {e}")
        return "\n".join(text_parts).strip()

    def calculate_ats_score(self, text: str,
                            target_role: str = "") -> Tuple[float, Dict]:
        """
        Returns (score 0-100, breakdown_dict).
        Scoring criteria:
          - Keyword presence       : 40 pts
          - Section completeness   : 25 pts
          - Formatting signals     : 20 pts
          - Length appropriateness : 15 pts
        """
        lower_text = text.lower()
        breakdown = {}

        # 1. Keyword score (40 pts)
        hits = [kw for kw in ATS_KEYWORDS if kw in lower_text]
        kw_score = min(40, (len(hits) / max(len(ATS_KEYWORDS), 1)) * 100 * 0.4)
        breakdown["keywords"] = {
            "score": round(kw_score, 1),
            "found": len(hits),
            "total": len(ATS_KEYWORDS),
            "matched": hits[:15],
        }

        # 2. Section completeness (25 pts)
        found_sections = [s for s in self.SECTION_HEADERS if s in lower_text]
        section_score = min(25, (len(found_sections) / 6) * 25)
        breakdown["sections"] = {
            "score": round(section_score, 1),
            "found": found_sections,
        }

        # 3. Formatting signals (20 pts)
        fmt_score = 0
        has_email   = bool(re.search(r"[\w.+-]+@[\w-]+\.\w+", text))
        has_phone   = bool(re.search(r"\+?\d[\d\s\-().]{7,15}\d", text))
        has_linkedin= "linkedin" in lower_text
        has_github  = "github" in lower_text
        has_bullets = text.count("•") + text.count("-") + text.count("*") > 5
        has_dates   = bool(re.search(r"\b(20\d{2}|19\d{2})\b", text))

        fmt_score += 4 if has_email else 0
        fmt_score += 3 if has_phone else 0
        fmt_score += 3 if has_linkedin else 0
        fmt_score += 2 if has_github else 0
        fmt_score += 4 if has_bullets else 0
        fmt_score += 4 if has_dates else 0
        breakdown["formatting"] = {
            "score": fmt_score,
            "email": has_email,
            "phone": has_phone,
            "linkedin": has_linkedin,
            "github": has_github,
            "bullets": has_bullets,
            "dates": has_dates,
        }

        # 4. Length appropriateness (15 pts)
        word_count = len(text.split())
        if 300 <= word_count <= 800:
            len_score = 15
        elif 200 <= word_count < 300 or 800 < word_count <= 1200:
            len_score = 10
        else:
            len_score = 5
        breakdown["length"] = {
            "score": len_score,
            "word_count": word_count,
        }

        total = kw_score + section_score + fmt_score + len_score
        return round(min(100, total), 1), breakdown

    def detect_skills(self, text: str) -> Dict[str, List[str]]:
        """Returns skills grouped by category."""
        lower_text = text.lower()
        result = {}
        all_found = []
        for category, skills in SKILL_CATEGORIES.items():
            found = [s for s in skills if s in lower_text]
            if found:
                result[category] = found
            all_found.extend(found)
        result["_all"] = all_found
        return result

    def find_missing_skills(self, text: str,
                            target_role: str = "Software Engineer") -> List[str]:
        """Return ATS keywords / skills absent from the resume."""
        lower_text = text.lower()
        missing = [kw for kw in ATS_KEYWORDS if kw not in lower_text]
        # Prioritise the most impactful ones
        high_priority = [
            "python", "sql", "git", "docker", "aws", "machine learning",
            "rest api", "agile", "communication", "problem solving"
        ]
        sorted_missing = sorted(
            missing,
            key=lambda k: (0 if k in high_priority else 1, k)
        )
        return sorted_missing[:15]

    def generate_suggestions(self, text: str,
                              ats_score: float,
                              missing: List[str]) -> List[str]:
        """Local rule-based suggestions (fallback when Gemini unavailable)."""
        suggestions = []
        lower = text.lower()

        if ats_score < 60:
            suggestions.append(
                "Critical: ATS score is below 60. Significantly revamp keywords "
                "and structure before applying."
            )
        if "linkedin" not in lower:
            suggestions.append(
                "Add your LinkedIn profile URL — most ATS systems look for it."
            )
        if "github" not in lower:
            suggestions.append(
                "Include your GitHub profile to showcase real projects and code."
            )
        if len(text.split()) < 250:
            suggestions.append(
                "Resume appears too short. Expand bullet points with metrics "
                "and achievements (target 400-700 words)."
            )
        if len(text.split()) > 1200:
            suggestions.append(
                "Resume may be too long for ATS. Condense to 1-2 pages."
            )
        if missing:
            top = ", ".join(missing[:5])
            suggestions.append(
                f"Add these high-value keywords where genuinely applicable: {top}."
            )
        if text.count("•") + text.count("-") < 5:
            suggestions.append(
                "Use bullet points for experience entries — ATS parsers handle "
                "them better than dense paragraphs."
            )
        if not re.search(r"\b\d+%|\b\d+x\b|\$\d+", text):
            suggestions.append(
                "Quantify achievements with numbers (e.g., 'reduced latency by 40%', "
                "'managed team of 5')."
            )
        if not suggestions:
            suggestions.append(
                "Resume looks solid! Focus on tailoring it for each specific job posting."
            )
        return suggestions[:8]

    def full_analysis(self, file_path: str,
                      target_role: str = "Software Engineer") -> Dict:
        """
        Orchestrates extraction → scoring → skill detection.
        Returns everything needed for the Resume page.
        """
        text = self.extract_text(file_path)
        ats_score, breakdown = self.calculate_ats_score(text, target_role)
        skills_by_cat = self.detect_skills(text)
        skills_found  = skills_by_cat.get("_all", [])
        missing       = self.find_missing_skills(text, target_role)
        suggestions   = self.generate_suggestions(text, ats_score, missing)

        return {
            "raw_text":       text,
            "ats_score":      ats_score,
            "ats_breakdown":  breakdown,
            "skills_found":   skills_found,
            "skills_by_cat":  {k: v for k, v in skills_by_cat.items() if k != "_all"},
            "missing_skills": missing,
            "suggestions":    suggestions,
        }


_resume_service: Optional[ResumeService] = None

def get_resume_service() -> ResumeService:
    global _resume_service
    if _resume_service is None:
        _resume_service = ResumeService()
    return _resume_service