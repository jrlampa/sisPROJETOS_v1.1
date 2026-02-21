import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

from styles import DesignSystem

from .logic import ProjectCreatorLogic


class ProjectCreatorGUI(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, **DesignSystem.get_frame_style())
        self.controller = controller
        self.logic = ProjectCreatorLogic()

        self.create_widgets()

    def create_widgets(self):
        # Header
        ctk.CTkLabel(
            self, text="Criador de Novos Projetos", font=DesignSystem.FONT_SUBHEAD, text_color=DesignSystem.TEXT_MAIN
        ).pack(pady=20)

        # Form
        self.form_frame = ctk.CTkFrame(
            self, fg_color="#F8FAFC", corner_radius=15, border_width=1, border_color="#E2E8F0"
        )
        self.form_frame.pack(pady=10, padx=40, fill="x")

        ctk.CTkLabel(self.form_frame, text="Nome do Projeto:", font=DesignSystem.FONT_BODY).pack(
            anchor="w", padx=20, pady=(20, 0)
        )
        self.entry_name = ctk.CTkEntry(
            self.form_frame, placeholder_text="Ex: PROJ-2024-001", **DesignSystem.get_entry_style()
        )
        self.entry_name.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.form_frame, text="Localização (Pasta Pai):", font=DesignSystem.FONT_BODY).pack(
            anchor="w", padx=20, pady=(10, 0)
        )

        self.path_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.path_frame.pack(fill="x", padx=20, pady=10)

        self.entry_path = ctk.CTkEntry(self.path_frame, **DesignSystem.get_entry_style())
        self.entry_path.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            self.path_frame,
            text="...",
            width=40,
            command=self.browse_folder,
            **DesignSystem.get_button_style("secondary"),
        ).pack(side="right", padx=(5, 0))

        # Create Button
        self.btn_create = ctk.CTkButton(
            self,
            text="Criar Estrutura do Projeto",
            command=self.create_project,
            **DesignSystem.get_button_style("primary"),
        )
        self.btn_create.pack(pady=30)

        # Status
        self.lbl_status = ctk.CTkLabel(self, text="", font=DesignSystem.FONT_BODY)
        self.lbl_status.pack(pady=5)

        # Back
        ctk.CTkButton(
            self,
            text="Voltar",
            command=lambda: self.controller.show_frame("Menu"),
            **DesignSystem.get_button_style("gray"),
        ).pack(side="bottom", pady=20)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, folder)

    def create_project(self):
        name = self.entry_name.get().strip()
        path = self.entry_path.get().strip()

        if not name or not path:
            messagebox.showwarning("Atenção", "Preencha o nome e o local do projeto.")
            return

        success, result = self.logic.create_structure(name, path)

        if success:
            self.lbl_status.configure(
                text=f"Projeto '{name}' criado com sucesso!", text_color=DesignSystem.ACCENT_SUCCESS
            )
            messagebox.showinfo("Sucesso", f"Estrutura criada em:\n{os.path.join(path, name)}")
        else:
            self.lbl_status.configure(text=result, text_color=DesignSystem.ACCENT_ERROR)
            messagebox.showerror("Erro", result)
