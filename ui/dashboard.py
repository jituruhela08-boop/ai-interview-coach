import customtkinter as ctk

from ui.sidebar import Sidebar

from pages.home_page import HomePage
from pages.resume_page import ResumePage
from pages.interview_page import InterviewPage
from pages.analytics_page import AnalyticsPage
from pages.settings_page import SettingsPage

from ui.theme import COLORS


class Dashboard(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=COLORS["bg"]
        )

        self.pack(fill="both", expand=True)

        self.sidebar = Sidebar(
            self,
            self.show_page
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.content = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg"]
        )

        self.content.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.pages = {}

        self.pages["home"] = HomePage(self.content)
        self.pages["resume"] = ResumePage(self.content)
        self.pages["interview"] = InterviewPage(self.content)
        self.pages["analytics"] = AnalyticsPage(self.content)
        self.pages["settings"] = SettingsPage(self.content)

        self.show_page("home")

    def show_page(self, page_name):

        for page in self.pages.values():
            page.pack_forget()

        self.pages[page_name].pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )