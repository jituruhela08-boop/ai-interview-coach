"""
config.py — Global Configuration, Theme Constants, and API Settings
AI Interview Coach | Premium SaaS Desktop Application
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────
#  PROJECT PATHS
# ─────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
ASSETS_DIR      = BASE_DIR / "assets"
DATABASE_DIR    = BASE_DIR / "database"
REPORTS_DIR     = BASE_DIR / "reports"
LOGS_DIR        = BASE_DIR / "logs"

DB_PATH         = DATABASE_DIR / "interview_coach.db"
LOG_PATH        = LOGS_DIR / "app.log"

# Ensure directories exist
for d in [ASSETS_DIR, DATABASE_DIR, REPORTS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
#  GOOGLE GEMINI API
# ─────────────────────────────────────────────
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")   # Set via env var or Settings page
GEMINI_MODEL    = "gemini-1.5-flash"

# ─────────────────────────────────────────────
#  APP META
# ─────────────────────────────────────────────
APP_NAME        = "AI Interview Coach"
APP_VERSION     = "2.0.0"
APP_TAGLINE     = "Powered by Gemini AI"
WINDOW_SIZE     = "1400x860"
MIN_SIZE        = (1200, 750)

# ─────────────────────────────────────────────
#  COLOR PALETTE  —  Dark Glassmorphism / Neon
# ─────────────────────────────────────────────
class Colors:
    # Backgrounds
    BG_PRIMARY      = "#090B15"      # Near-black navy — main background
    BG_SECONDARY    = "#0D1021"      # Slightly lighter — sidebar
    BG_CARD         = "#111428"      # Card surfaces
    BG_CARD_HOVER   = "#161B35"      # Card hover state
    BG_INPUT        = "#0F1324"      # Input fields
    BG_OVERLAY      = "#07091280"    # Modal overlays (semi-transparent)

    # Neon Accents
    NEON_CYAN       = "#00D4FF"      # Primary accent — cyan
    NEON_PURPLE     = "#8B5CF6"      # Secondary accent — violet
    NEON_BLUE       = "#3B82F6"      # Tertiary — blue
    NEON_PINK       = "#EC4899"      # Alert / warning
    NEON_GREEN      = "#10B981"      # Success / positive
    NEON_ORANGE     = "#F59E0B"      # Caution / medium

    # Glassmorphism Borders
    BORDER_DIM      = "#1E2440"      # Subtle border
    BORDER_GLOW     = "#2A3560"      # Slightly brighter border
    BORDER_CYAN     = "#00D4FF30"    # Cyan glow border
    BORDER_PURPLE   = "#8B5CF630"    # Purple glow border

    # Text
    TEXT_PRIMARY    = "#E8EEFF"      # Near-white — main text
    TEXT_SECONDARY  = "#7B8EC8"      # Muted — labels
    TEXT_MUTED      = "#3D4F7C"      # Very muted — placeholders
    TEXT_ACCENT     = "#00D4FF"      # Highlighted text

    # Gradients (used as start/end tuples for canvas gradients)
    GRAD_CYAN_PURPLE    = ("#00D4FF", "#8B5CF6")
    GRAD_PURPLE_PINK    = ("#8B5CF6", "#EC4899")
    GRAD_BLUE_CYAN      = ("#3B82F6", "#00D4FF")
    GRAD_GREEN_CYAN     = ("#10B981", "#00D4FF")

    # Chart Colors
    CHART_COLORS    = ["#00D4FF", "#8B5CF6", "#3B82F6", "#10B981",
                       "#F59E0B", "#EC4899", "#6366F1", "#14B8A6"]

    # Sidebar
    SIDEBAR_BG      = "#0A0D1E"
    SIDEBAR_ACTIVE  = "#1A1F3E"
    SIDEBAR_HOVER   = "#12163080"

    # Status
    SUCCESS         = "#10B981"
    WARNING         = "#F59E0B"
    ERROR           = "#EF4444"
    INFO            = "#3B82F6"

# ─────────────────────────────────────────────
#  TYPOGRAPHY
# ─────────────────────────────────────────────
class Fonts:
    FAMILY_PRIMARY  = "Segoe UI"
    FAMILY_MONO     = "Consolas"
    FAMILY_FALLBACK = "Arial"

    # Sizes
    XS      = 10
    SM      = 11
    BASE    = 12
    MD      = 13
    LG      = 14
    XL      = 16
    XXL     = 20
    XXXL    = 26
    HERO    = 34

    # Weights
    NORMAL  = "normal"
    BOLD    = "bold"

    # Pre-built tuples  (family, size, weight)
    HERO_TITLE      = (FAMILY_PRIMARY, HERO,  BOLD)
    PAGE_TITLE      = (FAMILY_PRIMARY, XXXL,  BOLD)
    SECTION_TITLE   = (FAMILY_PRIMARY, XL,    BOLD)
    CARD_TITLE      = (FAMILY_PRIMARY, LG,    BOLD)
    BODY            = (FAMILY_PRIMARY, BASE,  NORMAL)
    BODY_BOLD       = (FAMILY_PRIMARY, BASE,  BOLD)
    LABEL           = (FAMILY_PRIMARY, SM,    NORMAL)
    CAPTION         = (FAMILY_PRIMARY, XS,    NORMAL)
    MONO            = (FAMILY_MONO,    BASE,  NORMAL)
    METRIC          = (FAMILY_PRIMARY, XXXL,  BOLD)
    METRIC_SM       = (FAMILY_PRIMARY, XXL,   BOLD)
    NAV_ITEM        = (FAMILY_PRIMARY, MD,    NORMAL)
    NAV_ITEM_ACTIVE = (FAMILY_PRIMARY, MD,    BOLD)
    BUTTON          = (FAMILY_PRIMARY, MD,    BOLD)
    BUTTON_SM       = (FAMILY_PRIMARY, SM,    BOLD)

# ─────────────────────────────────────────────
#  DIMENSIONS & SPACING
# ─────────────────────────────────────────────
class Layout:
    SIDEBAR_WIDTH       = 220
    NAVBAR_HEIGHT       = 64
    CARD_CORNER_RADIUS  = 16
    BUTTON_CORNER_RADIUS= 10
    INPUT_CORNER_RADIUS = 8
    CARD_PADDING        = 20
    SECTION_GAP         = 16
    ITEM_GAP            = 12

# ─────────────────────────────────────────────
#  INTERVIEW CONFIGURATION
# ─────────────────────────────────────────────
INTERVIEW_MODES = ["Technical", "HR / Behavioral", "Mixed"]
DIFFICULTY_LEVELS = ["Junior", "Mid-level", "Senior", "Lead / Architect"]
QUESTION_COUNTS = [5, 10, 15, 20]

TECH_DOMAINS = [
    "Python", "JavaScript", "Java", "C++", "Go", "Rust",
    "React", "Node.js", "Django", "FastAPI", "Spring Boot",
    "Machine Learning", "Data Science", "DevOps / Cloud",
    "System Design", "Databases", "Cybersecurity", "Mobile Dev"
]

ATS_KEYWORDS = [
    "python", "javascript", "java", "sql", "react", "node.js", "docker",
    "kubernetes", "aws", "azure", "gcp", "machine learning", "deep learning",
    "tensorflow", "pytorch", "data analysis", "agile", "scrum", "git",
    "ci/cd", "microservices", "rest api", "graphql", "mongodb", "postgresql",
    "redis", "kafka", "spark", "hadoop", "tableau", "power bi", "excel",
    "communication", "leadership", "problem solving", "teamwork", "collaboration"
]

SKILL_CATEGORIES = {
    "Programming Languages": ["python", "javascript", "java", "c++", "go", "rust", "typescript"],
    "Web Frameworks":        ["react", "angular", "vue", "django", "fastapi", "flask", "node.js"],
    "Cloud & DevOps":        ["aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "terraform"],
    "Data & AI":             ["machine learning", "deep learning", "tensorflow", "pytorch", "sql", "spark"],
    "Soft Skills":           ["communication", "leadership", "teamwork", "problem solving", "agile"]
}

# ─────────────────────────────────────────────
#  CHART / ANALYTICS CONFIG
# ─────────────────────────────────────────────
MATPLOTLIB_STYLE = {
    "figure.facecolor":     "#090B15",
    "axes.facecolor":       "#111428",
    "axes.edgecolor":       "#1E2440",
    "axes.labelcolor":      "#7B8EC8",
    "axes.grid":            True,
    "grid.color":           "#1E2440",
    "grid.linestyle":       "--",
    "grid.alpha":           0.5,
    "xtick.color":          "#7B8EC8",
    "ytick.color":          "#7B8EC8",
    "text.color":           "#E8EEFF",
    "legend.facecolor":     "#111428",
    "legend.edgecolor":     "#1E2440",
    "legend.labelcolor":    "#E8EEFF",
    "font.family":          "DejaVu Sans",
    "font.size":            10,
}