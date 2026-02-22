from tkinter import filedialog, messagebox

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from styles import DesignSystem

from .logic import PoleLoadLogic
from .report import generate_report


class PoleLoadGUI(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, **DesignSystem.get_frame_style())
        self.controller = controller
        self.logic = PoleLoadLogic()
        self.cables = []  # List of cable widgets/data
        self.last_result = None
        self.last_inputs = None

        self.create_widgets()

    def create_widgets(self):
        # Layout: Left (Controls), Right (Result)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkScrollableFrame(
            self,
            width=480,
            label_text="Configuração do Poste",
            label_font=DesignSystem.FONT_SUBHEAD,
            fg_color="transparent",
        )
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(
            self, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0"
        )
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Controls Group
        self.params_frame = ctk.CTkFrame(
            self.left_frame, fg_color="#F8FAFC", corner_radius=15, border_width=1, border_color="#E2E8F0"
        )
        self.params_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            self.params_frame, text="Parâmetros Gerais", font=DesignSystem.FONT_BODY, text_color=DesignSystem.TEXT_DIM
        ).pack(pady=10)

        self.create_label_and_cmb(
            self.params_frame,
            "Concessionária:",
            self.logic.DADOS_CONCESSIONARIAS.keys(),
            self.update_options,
            "cmb_concess",
        )
        self.create_label_and_cmb(self.params_frame, "Condição:", ["Normal", "Vento Forte", "Gelo"], None, "cmb_cond")

        # Cables Section
        self.cables_header = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.cables_header.pack(fill="x", padx=10, pady=(20, 0))
        ctk.CTkLabel(
            self.cables_header,
            text="Condutores no Poste",
            font=DesignSystem.FONT_BODY,
            text_color=DesignSystem.TEXT_MAIN,
        ).pack(side="left")
        self.btn_add = ctk.CTkButton(
            self.cables_header,
            text="+ Cabo",
            width=80,
            height=30,
            command=self.add_cable_row,
            **DesignSystem.get_button_style("success"),
        )
        self.btn_add.pack(side="right")

        self.cables_container = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.cables_container.pack(fill="x", pady=10)

        # Actions Group
        self.actions_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.actions_frame.pack(fill="x", padx=10, pady=20)

        ctk.CTkButton(
            self.actions_frame,
            text="Calcular Esforço Resultante",
            command=self.calculate,
            **DesignSystem.get_button_style("primary"),
        ).pack(fill="x", pady=5)

        self.btn_suggest = ctk.CTkButton(
            self.actions_frame,
            text="Sugerir Poste Adequado",
            command=self.suggest_best_pole,
            state="disabled",
            **DesignSystem.get_button_style("purple"),
        )
        self.btn_suggest.pack(fill="x", pady=2)

        self.btn_report = ctk.CTkButton(
            self.actions_frame,
            text="Gerar Relatório PDF",
            command=self.generate_pdf,
            state="disabled",
            **DesignSystem.get_button_style("secondary"),
        )
        self.btn_report.pack(fill="x", pady=2)

        # Pole Verification
        self.pole_check_frame = ctk.CTkFrame(self.left_frame, fg_color="#F0F4F8", corner_radius=12)
        self.pole_check_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(
            self.pole_check_frame,
            text="Verificação de Segurança",
            font=DesignSystem.FONT_BODY,
            text_color=DesignSystem.TEXT_DIM,
        ).pack(pady=5)

        self.create_label_and_cmb(
            self.pole_check_frame,
            "Poste:",
            self.logic.DADOS_POSTES_NOMINAL.keys(),
            self.update_pole_specs,
            "cmb_pole_type",
        )
        self.create_label_and_cmb(self.pole_check_frame, "Capacidade:", [], None, "cmb_pole_spec")

        # Back
        ctk.CTkButton(
            self.left_frame,
            text="Voltar ao Menu",
            command=lambda: self.controller.show_frame("Menu"),
            **DesignSystem.get_button_style("gray"),
        ).pack(pady=20)

        # Plot Area
        self.fig, self.ax = plt.subplots(figsize=(5, 5), facecolor="white")
        self.ax.set_facecolor("#FAFAFA")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

        self.lbl_result = ctk.CTkLabel(
            self.right_frame,
            text="Diagrama de Vetores de Trações",
            font=DesignSystem.FONT_BODY,
            text_color=DesignSystem.TEXT_DIM,
        )
        self.lbl_result.pack(pady=20)

        self.update_options()
        self.update_pole_specs()

    def create_label_and_cmb(self, parent, label_text, values, cmd, attr_name):
        ctk.CTkLabel(parent, text=label_text, font=DesignSystem.FONT_BODY, text_color=DesignSystem.TEXT_MAIN).pack(
            anchor="w", padx=15
        )
        cmb = ctk.CTkComboBox(parent, values=list(values), command=cmd, **DesignSystem.get_entry_style())
        cmb.pack(fill="x", padx=15, pady=(0, 10))
        setattr(self, attr_name, cmb)

    def update_options(self, choice=None):
        # Refresh cable rows if needed? Or just let user re-select?
        # For simple version, just clear current cables if concessionaire changes might be better?
        # Leaving as is for now, user manually changes.
        pass

    def update_pole_specs(self, choice=None):
        ptype = self.cmb_pole_type.get()
        specs = list(self.logic.DADOS_POSTES_NOMINAL.get(ptype, {}).keys())
        self.cmb_pole_spec.configure(values=specs)
        if specs:
            self.cmb_pole_spec.set(specs[0])

    def add_cable_row(self):
        row = ctk.CTkFrame(self.cables_container)
        row.pack(fill="x", pady=2)

        concess = self.logic.DADOS_CONCESSIONARIAS.get(
            self.cmb_concess.get(), list(self.logic.DADOS_CONCESSIONARIAS.values())[0]
        )
        redes = list(concess["REDES_PARA_CONDUTORES"].keys())

        # simplified row: Network | Conductor | Span | Angle
        cmb_net = ctk.CTkComboBox(row, values=redes, width=100)
        cmb_net.pack(side="left", padx=2)

        cmb_cond = ctk.CTkComboBox(row, values=[], width=150)
        cmb_cond.pack(side="left", padx=2)

        def update_conds(c):
            net = cmb_net.get()
            conds = concess["REDES_PARA_CONDUTORES"].get(net, [])
            cmb_cond.configure(values=conds)
            if conds:
                cmb_cond.set(conds[0])

        cmb_net.configure(command=update_conds)
        if redes:
            cmb_net.set(redes[0])
            update_conds(None)

        entry_span = ctk.CTkEntry(row, placeholder_text="Vão (m)", width=60)
        entry_span.pack(side="left", padx=2)

        entry_angle = ctk.CTkEntry(row, placeholder_text="Ângulo", width=50)
        entry_angle.pack(side="left", padx=2)

        # Optional Flecha for Light
        entry_flecha = ctk.CTkEntry(row, placeholder_text="Flecha", width=50)
        # Only show if Light? For now show always for simplicity or hide?
        # Let's show it, logic handles if it's used.
        entry_flecha.pack(side="left", padx=2)

        # Del button
        ctk.CTkButton(row, text="X", width=30, fg_color="red", command=lambda: self.remove_row(row)).pack(side="right")

        self.cables.append(
            {
                "row": row,
                "net": cmb_net,
                "cond": cmb_cond,
                "span": entry_span,
                "ang": entry_angle,
                "flecha": entry_flecha,
            }
        )

    def remove_row(self, row):
        row.destroy()
        # Remove from list logic: find by row object
        self.cables = [c for c in self.cables if c["row"] != row]

    def calculate(self):
        inputs = []
        try:
            concess_name = self.cmb_concess.get()
            for c in self.cables:
                span_val = c["span"].get()
                ang_val = c["ang"].get()
                flecha_val = c["flecha"].get()

                if not span_val or not ang_val:
                    continue

                inputs.append(
                    {
                        "rede": c["net"].get(),
                        "condutor": c["cond"].get(),
                        "vao": float(span_val),
                        "angulo": float(ang_val),
                        "flecha": float(flecha_val) if flecha_val else 1.0,
                        "num_fases": 3,  # Default
                        "inclui_neutro": False,
                        "neutro_condutor": "",
                    }
                )

            res = self.logic.calculate_resultant(concess_name, self.cmb_cond.get(), inputs)

            if res:
                self.last_result = res
                self.last_inputs = inputs
                self.plot(res)
                ptype = self.cmb_pole_type.get()
                pspec = self.cmb_pole_spec.get()
                limit = self.logic.DADOS_POSTES_NOMINAL.get(ptype, {}).get(pspec, 0)

                status = "✅ APROVADO" if res["resultant_force"] <= limit else "❌ REPROVADO"
                color = "green" if res["resultant_force"] <= limit else "red"

                self.lbl_result.configure(
                    text=f"Força Resultante: {res['resultant_force']:.2f} daN\nÂngulo: {res['resultant_angle']:.2f}°\n\nLimite do Poste: {limit} daN\n{status}",
                    text_color=color,
                )
                self.btn_report.configure(state="normal")
                self.btn_suggest.configure(state="normal")
                # Share context with AI assistant
                self.controller.project_context["pole_load"] = res

        except ValueError:
            messagebox.showerror(
                "Erro", "Verifique se os campos numéricos (Vão, Ângulo, Flecha) estão preenchidos corretamente."
            )

    def generate_pdf(self):
        if not self.last_result:
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Document", "*.pdf")])
        if not filepath:
            return

        try:
            generate_report(filepath, self.last_inputs, self.last_result, project_name="Projeto Cabo sisPROJETOS")
            messagebox.showinfo("Sucesso", "Relatório PDF gerado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {str(e)}")

    def suggest_best_pole(self):
        if not self.last_result:
            return

        force = self.last_result["resultant_force"]
        suggestions = self.logic.suggest_pole(force)

        if not suggestions:
            messagebox.showinfo("Sugestão", "Nenhum poste no banco de dados suporta esta carga.")
            return

        msg = "Postes recomendados (mais leves por material):\n\n"
        for s in suggestions:
            msg += f"• {s['material']}: {s['description']} ({s['load']} daN)\n"

        msg += "\n\nDeseja aplicar a primeira sugestão automaticamente?"

        if messagebox.askyesno("Sugestão de Poste", msg):
            best = suggestions[0]
            self.cmb_pole_type.set(best["material"])
            self.update_pole_specs()
            self.cmb_pole_spec.set(best["description"])
            self.calculate()  # Re-calculate to show approved status

    def plot(self, data):
        self.ax.clear()

        # Vectors
        for v in data["vectors"]:
            self.ax.arrow(0, 0, v["fx"], v["fy"], head_width=2, color="blue", alpha=0.5)
            self.ax.text(v["fx"], v["fy"], v["name"], fontsize=8)

        # Resultant
        self.ax.arrow(
            0, 0, data["total_x"], data["total_y"], head_width=5, color="red", linewidth=2, label="Resultante"
        )

        max_val = max(abs(data["total_x"]), abs(data["total_y"]), 50) * 1.5
        self.ax.set_xlim(-max_val, max_val)
        self.ax.set_ylim(-max_val, max_val)
        self.ax.grid(True)
        self.ax.set_aspect("equal")
        self.ax.legend()
        self.ax.set_title("Diagrama de Forças")
        self.canvas.draw()
