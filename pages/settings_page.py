import customtkinter as ctk

class SettingsPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        title = ctk.CTkLabel(
            self,
            text="⚙ Settings",
            font=("Segoe UI",30,"bold")
        )

        title.pack(anchor="w", padx=20, pady=20)