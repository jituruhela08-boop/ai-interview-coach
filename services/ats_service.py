"""
services/ats_engine.py
Local ATS (Applicant Tracking System) scoring engine.
Works entirely offline — no API key required.
"""
import re
import logging
from config import ATS_KEYWORDS, SKILL_CATEGORIES

log = logging.getLogger(__name__)


def extract_text_from_pdf(filepath: str) -> str:
    """Extract plain text from a PDF file."""
    try:
        import PyPDF2
        text = ""
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        return text.strip()
    except ImportError:
        log.warning("PyPDF2 not installed. Attempting fallback.")
        return _fallback_pdf_read(filepath)
    except Exception as e:
        log.error("PDF extraction error: %s", e)
        return f"[PDF extraction error: {e}]"


def _fallback_pdf_read(filepath: str) -> str:
    """Attempt raw text extraction as fallback."""
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
        # Extract printable ASCII runs as crude text extraction
        text = re.findall(r'[A-Za-z0-9 \n\t.,;:@\-\(\)\/\+]{4,}', raw.decode("latin-1", errors="ignore"))
        return " ".join(text)
    except Exception as e:
        return f"[Cannot read PDF: {e}]"


def compute_ats_score(resume_text: str, job_description: str = "") -> dict:
    """
    Compute a comprehensive ATS score breakdown.
    Returns a dict with score, components, found/missing keywords, and category breakdown.
    """
    text_lower = resume_text.lower()
    jd_lower   = job_description.lower() if job_description else ""

    # ── keyword matching ──────────────────────────────
    found_keywords   = []
    missing_keywords = []
    for kw in ATS_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text_lower):
            found_keywords.append(kw)
        else:
            missing_keywords.append(kw)

    keyword_score = min(100, int(len(found_keywords) / max(len(ATS_KEYWORDS), 1) * 100))

    # ── skill category breakdown ───────────────────────
    category_scores = {}
    for cat, skills in SKILL_CATEGORIES.items():
        found = sum(1 for s in skills if s.lower() in text_lower)
        category_scores[cat] = int(found / max(len(skills), 1) * 100)

    # ── format / completeness checks ─────────────────
    has_email    = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resume_text))
    has_phone    = bool(re.search(r'[\+\(]?[\d\s\-\(\)]{9,}', resume_text))
    has_linkedin = "linkedin" in text_lower
    has_github   = "github" in text_lower

    sections = ["experience", "education", "skills", "projects", "summary", "objective"]
    found_sections = [s for s in sections if s in text_lower]

    format_score = int(
        (has_email    * 20) +
        (has_phone    * 15) +
        (has_linkedin * 10) +
        (has_github   * 10) +
        (len(found_sections) / len(sections) * 45)
    )

    # ── length / word density ─────────────────────────
    word_count   = len(resume_text.split())
    # Ideal range: 400–700 words; penalise below 200 or above 1200
    if 400 <= word_count <= 700:
        length_score = 100
    elif word_count < 200:
        length_score = int(word_count / 2)
    elif word_count > 1200:
        length_score = max(50, 100 - (word_count - 1200) // 20)
    else:
        length_score = min(100, int(word_count / 6))

    # ── job description match ─────────────────────────
    jd_score = 0
    if jd_lower:
        jd_words     = set(w for w in jd_lower.split() if len(w) > 3)
        resume_words = set(w for w in text_lower.split() if len(w) > 3)
        overlap      = len(jd_words & resume_words)
        jd_score     = min(100, int(overlap / max(len(jd_words), 1) * 200))

    # ── quantified achievement detection ─────────────
    quant_patterns = [
        r'\d+\s*%',                # percentages
        r'\$\s*\d+',               # dollar amounts
        r'\d+\s*(million|billion|k\b)',  # large numbers
        r'reduced\s+\w+\s+by',    # reduction claims
        r'increased\s+\w+\s+by',  # increase claims
        r'\d+\s+(users|customers|teams|engineers)',
    ]
    quant_count  = sum(1 for p in quant_patterns if re.search(p, text_lower))
    quant_score  = min(100, quant_count * 20)

    # ── composite score ───────────────────────────────
    if jd_lower:
        composite = (
            keyword_score * 0.25 +
            format_score  * 0.20 +
            length_score  * 0.10 +
            jd_score      * 0.35 +
            quant_score   * 0.10
        )
    else:
        composite = (
            keyword_score * 0.45 +
            format_score  * 0.30 +
            length_score  * 0.15 +
            quant_score   * 0.10
        )

    composite = min(100, round(composite, 1))

    return {
        "ats_score":        composite,
        "keyword_score":    keyword_score,
        "format_score":     format_score,
        "length_score":     length_score,
        "jd_match_score":   jd_score,
        "quant_score":      quant_score,
        "found_keywords":   found_keywords,
        "missing_keywords": missing_keywords[:15],
        "category_scores":  category_scores,
        "word_count":       word_count,
        "has_email":        has_email,
        "has_phone":        has_phone,
        "has_linkedin":     has_linkedin,
        "has_github":       has_github,
        "found_sections":   found_sections,
    }