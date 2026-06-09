import customtkinter as ctk

from ui.theme import apply_theme
from ui.dashboard import Dashboard

class AIInterviewCoach(ctk.CTk):

    def __init__(self):
        super().__init__()

        apply_theme()

        self.title("AI Interview Coach")
        self.geometry("1450x850")
        self.minsize(1300, 750)

        self.dashboard = Dashboard(self)
        self.dashboard.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = AIInterviewCoach()
    app.mainloop()