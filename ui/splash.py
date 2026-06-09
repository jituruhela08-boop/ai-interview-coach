"""
ui/splash.py — Animated Splash / Loading Screen
Displays while the app initialises database, services, and assets.
"""

import tkinter as tk
from typing import Callable

import customtkinter as ctk

from config import Colors, Fonts, APP_NAME, APP_VERSION, APP_TAGLINE, WINDOW_SIZE
from ui.theme import draw_gradient_rect


class SplashScreen(ctk.CTkToplevel):
    """
    Full-screen animated splash with:
    - Radial gradient background
    - Animated logo
    - Progress bar
    - Loading status text
    """
    WIDTH  = 680
    HEIGHT = 420

    def __init__(self, root: ctk.CTk, on_done: Callable):
        super().__init__(root)
        self._root    = root
        self._on_done = on_done
        self._progress = 0

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.resizable(False, False)

        # Center on screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - self.WIDTH)  // 2
        y  = (sh - self.HEIGHT) // 2
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self._build()
        self._animate_progress(0)

    def _build(self):
        # Background canvas with gradient
        self._canvas = tk.Canvas(
            self,
            width=self.WIDTH, height=self.HEIGHT,
            bg=Colors.BG_PRIMARY, highlightthickness=0,
        )
        self._canvas.pack(fill="both", expand=True)

        # Dark base
        self._canvas.create_rectangle(
            0, 0, self.WIDTH, self.HEIGHT,
            fill=Colors.BG_PRIMARY, outline=""
        )

        # Gradient glow effect — top-left corner
        for r in range(200, 0, -20):
            alpha_hex = format(max(0, min(255, int(r * 0.3))), "02x")
            self._canvas.create_oval(
                -r, -r, r, r,
                fill="", outline=Colors.NEON_PURPLE + alpha_hex, width=1
            )

        # Bottom-right glow
        for r in range(180, 0, -20):
            self._canvas.create_oval(
                self.WIDTH - r, self.HEIGHT - r,
                self.WIDTH + r, self.HEIGHT + r,
                fill="", outline=Colors.NEON_CYAN + "20", width=1
            )

        # Border frame
        self._canvas.create_rectangle(
            1, 1, self.WIDTH - 1, self.HEIGHT - 1,
            outline=Colors.BORDER_GLOW, width=1
        )

        # Robot/AI icon glow circle
        cx, cy = self.WIDTH // 2, 160
        for r in range(60, 0, -10):
            alpha = format(max(0, min(255, int(r * 2.5))), "02x")
            self._canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill="", outline=Colors.NEON_CYAN + alpha, width=1
            )

        # Icon
        self._canvas.create_text(
            cx, cy, text="🤖",
            font=("Arial", 44),
        )

        # App name
        self._canvas.create_text(
            cx, 220,
            text=APP_NAME,
            font=(Fonts.FAMILY_PRIMARY, 28, Fonts.BOLD),
            fill=Colors.TEXT_PRIMARY,
        )

        # Tagline
        self._canvas.create_text(
            cx, 254,
            text=APP_TAGLINE,
            font=(Fonts.FAMILY_PRIMARY, 12, Fonts.NORMAL),
            fill=Colors.NEON_CYAN,
        )

        # Version
        self._canvas.create_text(
            cx, 278,
            text=f"v{APP_VERSION}",
            font=(Fonts.FAMILY_PRIMARY, 9, Fonts.NORMAL),
            fill=Colors.TEXT_MUTED,
        )

        # Progress track
        pb_x0, pb_y0 = 120, 318
        pb_x1, pb_y1 = self.WIDTH - 120, 330
        self._canvas.create_rectangle(
            pb_x0, pb_y0, pb_x1, pb_y1,
            fill=Colors.BORDER_DIM, outline=Colors.BORDER_GLOW, width=1
        )

        # Progress fill (will be updated)
        self._pb_id = self._canvas.create_rectangle(
            pb_x0 + 1, pb_y0 + 1, pb_x0 + 2, pb_y1 - 1,
            fill=Colors.NEON_CYAN, outline="",
        )
        self._pb_x0    = pb_x0
        self._pb_x1    = pb_x1
        self._pb_y0    = pb_y0
        self._pb_y1    = pb_y1

        # Status text
        self._status_id = self._canvas.create_text(
            cx, 350,
            text="Initialising…",
            font=(Fonts.FAMILY_PRIMARY, 10, Fonts.NORMAL),
            fill=Colors.TEXT_MUTED,
        )

        # Copyright
        self._canvas.create_text(
            cx, self.HEIGHT - 20,
            text="© 2025 AI Interview Coach  •  All rights reserved",
            font=(Fonts.FAMILY_PRIMARY, 8, Fonts.NORMAL),
            fill=Colors.TEXT_MUTED,
        )

    def _animate_progress(self, step: int):
        """Increments progress bar in steps, then calls on_done."""
        steps = [
            (15,  "Loading configuration…"),
            (30,  "Connecting to database…"),
            (50,  "Initialising AI services…"),
            (65,  "Loading UI components…"),
            (80,  "Applying theme…"),
            (95,  "Almost ready…"),
            (100, "Welcome! 🚀"),
        ]
        if step >= len(steps):
            self.after(400, self._finish)
            return

        pct, msg = steps[step]
        self._set_progress(pct, msg)
        self.after(280, lambda: self._animate_progress(step + 1))

    def _set_progress(self, pct: float, msg: str = ""):
        fill_x1 = self._pb_x0 + (self._pb_x1 - self._pb_x0) * (pct / 100)
        self._canvas.coords(
            self._pb_id,
            self._pb_x0 + 1, self._pb_y0 + 1,
            fill_x1, self._pb_y1 - 1,
        )
        if msg:
            self._canvas.itemconfig(self._status_id, text=msg)

    def _finish(self):
        self.destroy()
        self._on_done()