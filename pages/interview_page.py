import customtkinter as ctk

class InterviewPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        title = ctk.CTkLabel(
            self,
            text="🎤 Mock Interview",
            font=("Segoe UI", 30, "bold")
        )

        title.pack(anchor="w", padx=20, pady=20)

        question = ctk.CTkTextbox(
            self,
            width=800,
            height=120
        )

        question.insert(
            "1.0",
            "Question will appear here..."
        )

        question.pack(pady=20)

        answer = ctk.CTkTextbox(
            self,
            width=800,
            height=250
        )

        answer.pack()

        submit = ctk.CTkButton(
            self,
            text="Submit Answer",
            height=50
        )

        submit.pack(pady=20)