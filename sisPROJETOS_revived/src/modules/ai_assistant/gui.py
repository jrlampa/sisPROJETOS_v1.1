import threading

import customtkinter as ctk

from styles import DesignSystem

from .logic import AIAssistantLogic


class AIAssistantGUI(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, **DesignSystem.get_frame_style())
        self.controller = controller
        self.logic = AIAssistantLogic()
        self.history = []

        self.create_widgets()

    def create_widgets(self):
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Assistente Técnico IA (Groq)",
            font=DesignSystem.FONT_SUBHEAD,
            text_color=DesignSystem.TEXT_MAIN,
        )
        self.header.grid(row=0, column=0, pady=20)

        # Chat area
        self.chat_area = ctk.CTkTextbox(
            self,
            state="disabled",
            wrap="word",
            font=DesignSystem.FONT_BODY,
            fg_color="white",
            text_color=DesignSystem.TEXT_MAIN,
            border_width=1,
            border_color="#E2E8F0",
        )
        self.chat_area.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)

        # Input area
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=20)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry_msg = ctk.CTkEntry(
            self.input_frame, placeholder_text="Digite sua dúvida técnica aqui...", **DesignSystem.get_entry_style()
        )
        self.entry_msg.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_msg.bind("<Return>", lambda e: self.send_message())

        self.btn_send = ctk.CTkButton(
            self.input_frame,
            text="Enviar",
            width=100,
            command=self.send_message,
            **DesignSystem.get_button_style("primary"),
        )
        self.btn_send.grid(row=0, column=1)

        # Bottom Controls
        self.ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ctrl_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=(0, 30))

        ctk.CTkButton(
            self.ctrl_frame, text="Limpar Chat", command=self.clear_chat, **DesignSystem.get_button_style("gray")
        ).pack(side="left")
        ctk.CTkButton(
            self.ctrl_frame,
            text="Voltar ao Menu",
            command=lambda: self.controller.show_frame("Menu"),
            **DesignSystem.get_button_style("secondary"),
        ).pack(side="right")

    def append_text(self, sender, text):
        self.chat_area.configure(state="normal")
        self.chat_area.insert("end", f"\n{sender}: ", ("bold",))
        self.chat_area.insert("end", f"{text}\n")
        self.chat_area.tag_config("bold", font=("Roboto", 13, "bold"))
        self.chat_area.configure(state="disabled")
        self.chat_area.see("end")

    def send_message(self):
        msg = self.entry_msg.get().strip()
        if not msg:
            return

        self.append_text("Você", msg)
        self.entry_msg.delete(0, "end")

        # Disable input while waiting
        self.btn_send.configure(state="disabled")
        self.entry_msg.configure(state="disabled")

        # Run API call in thread to avoid freezing GUI
        thread = threading.Thread(target=self.process_ai_response, args=(msg,))
        thread.start()

    def process_ai_response(self, msg):
        response = self.logic.get_response(msg, self.history, project_context=self.controller.project_context)

        # Update UI in main thread (using after)
        self.after(0, lambda: self.update_with_response(msg, response))

    def update_with_response(self, user_msg, ai_response):
        self.append_text("IA", ai_response)
        self.history.append((user_msg, ai_response))

        self.btn_send.configure(state="normal")
        self.entry_msg.configure(state="normal")
        self.entry_msg.focus_set()

    def clear_chat(self):
        self.chat_area.configure(state="normal")
        self.chat_area.delete("1.0", "end")
        self.chat_area.configure(state="disabled")
        self.history = []
