"""utils/helpers.py — Shared helper utilities for AI Interview Coach"""
from datetime import datetime


def format_duration(seconds: int) -> str:
    """Convert seconds to MM:SS or H:MM:SS string."""
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def score_to_grade(score: float):
    """Return (grade_letter, color_hex) for a 0–10 score."""
    if score >= 9:  return ("A+", "#10B981")
    if score >= 8:  return ("A",  "#10B981")
    if score >= 7:  return ("B+", "#3B82F6")
    if score >= 6:  return ("B",  "#3B82F6")
    if score >= 5:  return ("C",  "#F59E0B")
    if score >= 4:  return ("D",  "#F59E0B")
    return              ("F",  "#EF4444")


def ats_score_label(score: float):
    """Return (label, color_hex) for an ATS score 0–100."""
    if score >= 80: return ("Excellent", "#10B981")
    if score >= 65: return ("Good",      "#3B82F6")
    if score >= 50: return ("Fair",      "#F59E0B")
    return               ("Poor",      "#EF4444")


def truncate(text: str, length: int = 80) -> str:
    return text if len(text) <= length else text[:length - 3] + "…"


def relative_time(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        delta = datetime.now() - dt
        if delta.days == 0:
            h = delta.seconds // 3600
            if h == 0:
                m = delta.seconds // 60
                return f"{m}m ago" if m > 0 else "just now"
            return f"{h}h ago"
        if delta.days == 1:
            return "yesterday"
        if delta.days < 7:
            return f"{delta.days}d ago"
        if delta.days < 30:
            return f"{delta.days // 7}w ago"
        return dt.strftime("%b %d, %Y")
    except Exception:
        return iso_str[:10] if iso_str else ""