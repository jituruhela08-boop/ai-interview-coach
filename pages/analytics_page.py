import customtkinter as ctk

class AnalyticsPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        title = ctk.CTkLabel(
            self,
            text="📊 Analytics",
            font=("Segoe UI", 30, "bold")
        )

        title.pack(anchor="w", padx=20, pady=20)

        graph_placeholder = ctk.CTkFrame(
            self,
            width=900,
            height=450
        )

        graph_placeholder.pack(pady=30)

        graph_placeholder.pack_propagate(False)

        ctk.CTkLabel(
            graph_placeholder,
            text="Performance Graph Coming Soon",
            font=("Segoe UI",20)
        ).pack(expand=True)