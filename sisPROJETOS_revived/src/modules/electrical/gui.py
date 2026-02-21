from tkinter import messagebox

import customtkinter as ctk

from styles import DesignSystem

from .logic import ElectricalLogic


class ElectricalGUI(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, **DesignSystem.get_frame_style())
        self.controller = controller
        self.logic = ElectricalLogic()
        self.create_widgets()

    def create_widgets(self):
        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Cálculo de Queda de Tensão (BT)",
            font=DesignSystem.FONT_SUBHEAD,
            text_color=DesignSystem.TEXT_MAIN,
        )
        self.header.pack(pady=20)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(padx=20, pady=10, fill="both", expand=True)

        # Left Column: Inputs
        self.left_col = ctk.CTkFrame(self.container, fg_color="transparent")
        self.left_col.pack(side="left", padx=10, fill="y", expand=True)

        self.ent_power = self.create_field(self.left_col, "Potência Instalada (kW):", "10")
        self.ent_dist = self.create_field(self.left_col, "Distância (m):", "50")
        self.cmb_voltage = self.create_combo(self.left_col, "Tensão Nominal (V):", ["220", "127", "380"], "220")

        # Right Column: Conductors and Phases
        self.right_col = ctk.CTkFrame(self.container, fg_color="transparent")
        self.right_col.pack(side="left", padx=10, fill="y", expand=True)

        self.cmb_mat = self.create_combo(self.right_col, "Material do Condutor:", ["Alumínio", "Cobre"], "Alumínio")
        self.cmb_sec = self.create_combo(
            self.right_col, "Seção (mm²):", ["10", "16", "25", "35", "50", "70", "95", "120"], "16"
        )
        self.cmb_phases = self.create_combo(
            self.right_col, "Fases:", ["3 (Trifásico)", "1 (Monofásico)"], "3 (Trifásico)"
        )

        # Buttons
        self.btn_calc = ctk.CTkButton(
            self, text="Calcular", command=self.calculate, **DesignSystem.get_button_style("primary")
        )
        self.btn_calc.pack(pady=10)

        # Results Display Area
        self.res_frame = ctk.CTkFrame(
            self, fg_color="#F8FAFC", corner_radius=15, border_width=1, border_color="#E2E8F0"
        )
        self.res_frame.pack(pady=15, padx=30, fill="x")

        self.lbl_res = ctk.CTkLabel(
            self.res_frame,
            text="Insira os dados e clique em Calcular",
            font=DesignSystem.FONT_BODY,
            text_color=DesignSystem.TEXT_DIM,
        )
        self.lbl_res.pack(pady=20)

        self.btn_back = ctk.CTkButton(
            self,
            text="Voltar ao Menu",
            width=150,
            command=lambda: self.controller.show_frame("Menu"),
            **DesignSystem.get_button_style("gray"),
        )
        self.btn_back.pack(pady=10)

    def create_field(self, parent, label, default):
        ctk.CTkLabel(parent, text=label, font=DesignSystem.FONT_BODY, text_color=DesignSystem.TEXT_MAIN).pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        ent = ctk.CTkEntry(parent, **DesignSystem.get_entry_style())
        ent.insert(0, default)
        ent.pack(fill="x", padx=10, pady=5)
        return ent

    def create_combo(self, parent, label, values, default):
        ctk.CTkLabel(parent, text=label, font=DesignSystem.FONT_BODY, text_color=DesignSystem.TEXT_MAIN).pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        cmb = ctk.CTkComboBox(parent, values=values, **DesignSystem.get_entry_style())
        cmb.set(default)
        cmb.pack(fill="x", padx=10, pady=5)
        return cmb

    def calculate(self):
        try:
            power = self.ent_power.get()
            dist = self.ent_dist.get()
            volt = self.cmb_voltage.get()
            mat = self.cmb_mat.get()
            sec = self.cmb_sec.get()
            phases = 3 if "3" in self.cmb_phases.get() else 1

            res = self.logic.calculate_voltage_drop(power, dist, volt, mat, sec, phases=phases)

            if res:
                color = DesignSystem.ACCENT_SUCCESS if res["allowed"] else DesignSystem.ACCENT_ERROR
                status = "✅ DENTRO DO LIMITE (5%)" if res["allowed"] else "❌ FORA DO LIMITE (>5%)"

                txt = (
                    f"Corrente: {res['current']:.2f} A\n"
                    f"Queda de Tensão: {res['delta_v_volts']:.2f} V\n"
                    f"Percentual: {res['percentage_drop']:.2f}%\n\n"
                    f"{status}"
                )
                self.lbl_res.configure(text=txt, text_color=color)
                # Share context with AI
                self.controller.project_context["electrical"] = res
            else:
                messagebox.showerror("Erro", "Verifique os valores de entrada")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
