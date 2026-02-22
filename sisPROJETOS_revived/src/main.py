import threading
import webbrowser
from datetime import datetime, timezone
from tkinter import messagebox

import customtkinter as ctk

from __version__ import __version__
from database.db_manager import DatabaseManager
from modules.ai_assistant.gui import AIAssistantGUI
from modules.catenaria.gui import CatenaryGUI
from modules.converter.gui import ConverterGUI
from modules.cqt.gui import CQTGUI
from modules.electrical.gui import ElectricalGUI
from modules.pole_load.gui import PoleLoadGUI
from modules.project_creator.gui import ProjectCreatorGUI
from modules.settings.gui import SettingsGUI
from styles import DesignSystem
from utils.logger import get_logger
from utils.update_checker import UpdateChecker

logger = get_logger(__name__)


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()

        self.title(f"sisPROJETOS - Engenharia e Projetos v{__version__}")
        self.geometry("1100x750")
        self.configure(fg_color=DesignSystem.BG_WINDOW)

        # Shared Project Context for AI Integration
        self.project_context = {
            "pole_load": None,
            "catenary": None,
            "electrical": None,
            "cqt": None,
            "converter": None,
        }

        # Set theme to Light as per user request for glassmorphism
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        # Configure grid for container to allow stacking
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        # Initialize Menu
        # We need to pass self (controller) to frames
        for F in (
            MenuFrame,
            ConverterGUI,
            CatenaryGUI,
            ProjectCreatorGUI,
            PoleLoadGUI,
            AIAssistantGUI,
            SettingsGUI,
            ElectricalGUI,
            CQTGUI,
        ):
            page_name = F.__name__.replace("GUI", "").replace("Frame", "")
            if page_name == "Menu":
                page_name = "Menu"
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Menu")
        logger.info(f"sisPROJETOS iniciado - versão {__version__}")
        self.after(1200, self.check_updates_on_startup)

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        logger.debug(f"Navegação para frame: {frame_name}")
        frame.tkraise()
        # Pack if not already packed or using grid layout (simple pack for now)
        # We need to hide others. simpler: destroy and recreate or just pack_forget.
        # Let's use grid stacking.
        frame.grid(row=0, column=0, sticky="nsew")

    def check_updates_on_startup(self):
        settings = self.db.get_update_settings()
        if not settings["enabled"]:
            logger.info("Verificação de atualização desativada pelo usuário")
            return

        checker = UpdateChecker(current_version=__version__)
        if not checker.should_check_now(settings["last_checked"], settings["interval_days"]):
            logger.debug("Verificação de atualização ignorada por intervalo")
            return

        def worker():
            result = checker.check_for_updates(channel=settings["channel"])
            checked_at = datetime.now(timezone.utc).isoformat()
            self.db.save_update_settings(last_checked=checked_at)
            self.after(0, lambda: self._handle_update_result(result))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_update_result(self, result):
        if not result.available:
            logger.debug(f"Nenhuma atualização disponível: {result.reason}")
            return

        logger.info(f"Nova versão disponível: {result.latest_version}")
        answer = messagebox.askyesno(
            "Atualização disponível",
            f"Nova versão disponível: {result.latest_version}\n\nDeseja abrir a página de download?",
        )
        if answer and result.release_url:
            webbrowser.open(result.release_url)


class MenuFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, **DesignSystem.get_frame_style())
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        self.label = ctk.CTkLabel(
            self, text="sisPROJETOS - Menu Principal", font=DesignSystem.FONT_HEAD, text_color=DesignSystem.TEXT_MAIN
        )
        self.label.pack(pady=40)

        # Container for buttons to center them
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(expand=True)

        btn_width = 320
        btn_spacing = 12

        # Define button configurations
        menu_items = [
            ("1. Criador de Novos Projetos", "ProjectCreator", "primary"),
            ("2. Catenária (Flecha e Tração)", "Catenary", "primary"),
            ("3. Cálculo de Esforço no Poste", "PoleLoad", "primary"),
            ("4. Conversor KMZ -> UTM", "Converter", "primary"),
            ("5. Assistente Técnico IA", "AIAssistant", "secondary"),
            ("6. Configurações e Cadastros", "Settings", "gray"),
            ("7. Cálculo de Queda de Tensão", "Electrical", "purple"),
            ("8. Cadastro de CQT / QTOS", "CQT", "purple"),
        ]

        for text, frame_name, style_key in menu_items:
            btn = ctk.CTkButton(
                btn_container,
                text=text,
                width=btn_width,
                height=45,
                command=lambda f=frame_name: self.controller.show_frame(f),
                **DesignSystem.get_button_style(style_key),
            )
            btn.pack(pady=btn_spacing)

        self.btn_exit = ctk.CTkButton(
            self,
            text="Sair do Sistema",
            width=200,
            height=40,
            command=self.controller.quit,
            **DesignSystem.get_button_style("error"),
        )
        self.btn_exit.pack(pady=40)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
