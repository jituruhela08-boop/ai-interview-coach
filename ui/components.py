import customtkinter as ctk
from ui.theme import COLORS


class GlassCard(ctk.CTkFrame):

    def __init__(
        self,
        parent,
        width=250,
        height=150
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            fg_color=COLORS["card"],
            corner_radius=20,
            border_width=1,
            border_color="#222A45"
        )

        self.pack_propagate(False)


class SectionTitle(ctk.CTkLabel):

    def __init__(self, parent, text):
        super().__init__(
            parent,
            text=text,
            font=("Segoe UI", 24, "bold"),
            text_color="white"
        )


class StatCard(GlassCard):

    def __init__(
        self,
        parent,
        title,
        value,
        color="#6D5DFE"
    ):
        super().__init__(
            parent,
            width=250,
            height=140
        )

        self.title = ctk.CTkLabel(
            self,
            text=title,
            font=("Segoe UI", 13),
            text_color="#94A3B8"
        )

        self.title.pack(
            anchor="w",
            padx=20,
            pady=(20,5)
        )

        self.value = ctk.CTkLabel(
            self,
            text=value,
            font=("Segoe UI", 32, "bold"),
            text_color=color
        )

        self.value.pack(
            anchor="w",
            padx=20
        )


class SearchBar(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(
            parent,
            fg_color=COLORS["card"],
            height=60,
            corner_radius=15
        )

        self.pack_propagate(False)

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="Search...",
            border_width=0,
            height=40
        )

        self.entry.pack(
            fill="x",
            expand=True,
            padx=15,
            pady=10
        )

class GlowStatCard(GlassCard):

    def __init__(
        self,
        parent,
        title,
        value,
        color
    ) -> None:
        super().__init__(
            parent,
            width=250,
            height=140
        )

        self.configure(
            border_color=color,
            border_width=2
        )

        ctk.CTkLabel(
            self,
            text=title,
            text_color="#94A3B8",
            font=("Segoe UI",13)
        ).pack(
            anchor="w",
            padx=20,
            pady=(18,5)
        )

        ctk.CTkLabel(
            self,
            text=value,
            text_color=color,
            font=("Segoe UI",30,"bold")
        ).pack(
            anchor="w",
            padx=20
        )