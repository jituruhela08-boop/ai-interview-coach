"""
ui/theme.py — CustomTkinter Theme Engine
Applies the dark glassmorphism neon theme globally.
"""

import customtkinter as ctk
from config import Colors, Fonts, Layout


def apply_theme():
    """Configure CustomTkinter appearance for the premium dark theme."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    # Override CTk internal theme colors at module level
    # (CustomTkinter reads these from its internal JSON — we patch after init)


def configure_widget_defaults():
    """
    Set default styling options for CTk widget classes.
    Call once after ctk.CTk() is instantiated.
    """
    # These are applied via option_add so all future widgets inherit them
    pass  # Handled per-widget in components.py


# ─────────────────────────────────────────────
#  Gradient canvas helper (used in multiple places)
# ─────────────────────────────────────────────
def draw_gradient_rect(canvas, x1, y1, x2, y2,
                        color1: str, color2: str,
                        steps: int = 60, direction: str = "horizontal"):
    """
    Draw a smooth gradient rectangle on a tkinter Canvas widget.
    direction: 'horizontal' | 'vertical'
    """
    def hex_to_rgb(h: str):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(r, g, b):
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)

    for i in range(steps):
        t = i / steps
        r = r1 + (r2 - r1) * t
        g = g1 + (g2 - g1) * t
        b = b1 + (b2 - b1) * t
        col = rgb_to_hex(r, g, b)
        if direction == "horizontal":
            chunk_x1 = x1 + (x2 - x1) * (i / steps)
            chunk_x2 = x1 + (x2 - x1) * ((i + 1) / steps)
            canvas.create_rectangle(chunk_x1, y1, chunk_x2, y2,
                                     fill=col, outline="", tags="gradient")
        else:
            chunk_y1 = y1 + (y2 - y1) * (i / steps)
            chunk_y2 = y1 + (y2 - y1) * ((i + 1) / steps)
            canvas.create_rectangle(x1, chunk_y1, x2, chunk_y2,
                                     fill=col, outline="", tags="gradient")


# ─────────────────────────────────────────────
#  Score colour helper
# ─────────────────────────────────────────────
def score_color(score: float) -> str:
    """Return neon colour matching score bucket."""
    if score >= 80:
        return Colors.NEON_GREEN
    elif score >= 60:
        return Colors.NEON_CYAN
    elif score >= 40:
        return Colors.NEON_ORANGE
    else:
        return Colors.NEON_PINK


def priority_color(priority: str) -> str:
    mapping = {
        "High":   Colors.NEON_PINK,
        "Medium": Colors.NEON_ORANGE,
        "Low":    Colors.NEON_GREEN,
    }
    return mapping.get(priority, Colors.TEXT_SECONDARY)