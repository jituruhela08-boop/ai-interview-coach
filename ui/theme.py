"""
ui/theme.py
Applies the dark glassmorphism neon theme to CustomTkinter.
Called once at startup in main.py: apply_theme()
"""
import customtkinter as ctk
from config import Colors


def apply_theme() -> None:
    """
    Configure the global CustomTkinter appearance.
    Sets dark mode and injects the neon cyan/purple colour palette.
    """
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


# ─── Reusable widget factory helpers ────────────────────────────────────────
# These are used across all pages to ensure visual consistency.

def make_card(parent, **kwargs) -> ctk.CTkFrame:
    """Returns a styled glassmorphism card frame."""
    defaults = dict(
        fg_color      = Colors.BG_CARD,
        corner_radius = 16,
        border_width  = 1,
        border_color  = Colors.BORDER_DIM,
    )
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def make_neon_button(parent, text: str, command=None,
                     color: str = Colors.NEON_CYAN, **kwargs) -> ctk.CTkButton:
    """Returns a neon-accented CTA button."""
    defaults = dict(
        text             = text,
        command          = command,
        fg_color         = color,
        hover_color      = _darken(color, 0.85),
        text_color       = Colors.BG_PRIMARY,
        corner_radius    = 10,
        font             = ("Segoe UI", 13, "bold"),
        height           = 40,
    )
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)


def make_ghost_button(parent, text: str, command=None,
                      color: str = Colors.NEON_CYAN, **kwargs) -> ctk.CTkButton:
    """Returns a ghost/outlined button."""
    defaults = dict(
        text          = text,
        command       = command,
        fg_color      = "transparent",
        hover_color   = Colors.BG_CARD_HOVER,
        text_color    = color,
        border_width  = 1,
        border_color  = color,
        corner_radius = 10,
        font          = ("Segoe UI", 12, "normal"),
        height        = 36,
    )
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)


def make_label(parent, text: str, style: str = "body", **kwargs) -> ctk.CTkLabel:
    """
    Returns a styled label.
    style: 'hero' | 'page_title' | 'section' | 'card_title' |
           'body' | 'label' | 'caption' | 'accent' | 'muted' | 'metric'
    """
    _styles = {
        "hero":       (Colors.TEXT_PRIMARY,   ("Segoe UI", 34, "bold")),
        "page_title": (Colors.TEXT_PRIMARY,   ("Segoe UI", 26, "bold")),
        "section":    (Colors.TEXT_PRIMARY,   ("Segoe UI", 16, "bold")),
        "card_title": (Colors.TEXT_PRIMARY,   ("Segoe UI", 14, "bold")),
        "body":       (Colors.TEXT_SECONDARY, ("Segoe UI", 12, "normal")),
        "label":      (Colors.TEXT_SECONDARY, ("Segoe UI", 11, "normal")),
        "caption":    (Colors.TEXT_MUTED,     ("Segoe UI", 10, "normal")),
        "accent":     (Colors.NEON_CYAN,      ("Segoe UI", 13, "bold")),
        "muted":      (Colors.TEXT_MUTED,     ("Segoe UI", 11, "normal")),
        "metric":     (Colors.NEON_CYAN,      ("Segoe UI", 26, "bold")),
    }
    color, font = _styles.get(style, _styles["body"])
    defaults = dict(text=text, text_color=color, font=font)
    defaults.update(kwargs)
    return ctk.CTkLabel(parent, **defaults)


def make_input(parent, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
    """Returns a styled input field."""
    defaults = dict(
        placeholder_text       = placeholder,
        fg_color               = Colors.BG_INPUT,
        border_color           = Colors.BORDER_DIM,
        border_width           = 1,
        text_color             = Colors.TEXT_PRIMARY,
        placeholder_text_color = Colors.TEXT_MUTED,
        corner_radius          = 8,
        font                   = ("Segoe UI", 12, "normal"),
        height                 = 38,
    )
    defaults.update(kwargs)
    return ctk.CTkEntry(parent, **defaults)


def make_textbox(parent, **kwargs) -> ctk.CTkTextbox:
    """Returns a styled multi-line textbox."""
    defaults = dict(
        fg_color      = Colors.BG_INPUT,
        border_color  = Colors.BORDER_DIM,
        border_width  = 1,
        text_color    = Colors.TEXT_PRIMARY,
        corner_radius = 8,
        font          = ("Segoe UI", 12, "normal"),
    )
    defaults.update(kwargs)
    return ctk.CTkTextbox(parent, **defaults)


def make_dropdown(parent, values: list, **kwargs) -> ctk.CTkOptionMenu:
    """Returns a styled dropdown/option menu."""
    defaults = dict(
        values         = values,
        fg_color       = Colors.BG_INPUT,
        button_color   = Colors.BG_CARD,
        button_hover_color = Colors.BG_CARD_HOVER,
        text_color     = Colors.TEXT_PRIMARY,
        dropdown_fg_color     = Colors.BG_CARD,
        dropdown_text_color   = Colors.TEXT_PRIMARY,
        dropdown_hover_color  = Colors.BG_CARD_HOVER,
        corner_radius  = 8,
        font           = ("Segoe UI", 12, "normal"),
        height         = 38,
    )
    defaults.update(kwargs)
    return ctk.CTkOptionMenu(parent, **defaults)


def make_progress_bar(parent, **kwargs) -> ctk.CTkProgressBar:
    """Returns a styled progress bar."""
    defaults = dict(
        progress_color = Colors.NEON_CYAN,
        fg_color       = Colors.BORDER_DIM,
        corner_radius  = 4,
        height         = 6,
    )
    defaults.update(kwargs)
    return ctk.CTkProgressBar(parent, **defaults)


def make_scrollable_frame(parent, **kwargs) -> ctk.CTkScrollableFrame:
    """Returns a styled scrollable frame."""
    defaults = dict(
        fg_color      = "transparent",
        scrollbar_fg_color      = Colors.BG_CARD,
        scrollbar_button_color  = Colors.BORDER_DIM,
        scrollbar_button_hover_color = Colors.BORDER_GLOW,
        corner_radius = 0,
    )
    defaults.update(kwargs)
    return ctk.CTkScrollableFrame(parent, **defaults)


def make_separator(parent, orientation: str = "horizontal") -> ctk.CTkFrame:
    """Returns a thin separator line."""
    if orientation == "horizontal":
        return ctk.CTkFrame(parent, height=1, fg_color=Colors.BORDER_DIM, corner_radius=0)
    return ctk.CTkFrame(parent, width=1, fg_color=Colors.BORDER_DIM, corner_radius=0)


def make_badge(parent, text: str, color: str = Colors.NEON_CYAN) -> ctk.CTkLabel:
    """Returns a small coloured badge label."""
    return ctk.CTkLabel(
        parent, text=f"  {text}  ",
        fg_color=f"{color}22",
        text_color=color,
        corner_radius=6,
        font=("Segoe UI", 10, "bold"),
    )


def _darken(hex_color: str, factor: float) -> str:
    """Darken a hex colour by a given factor (0–1)."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color