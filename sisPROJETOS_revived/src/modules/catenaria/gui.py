import customtkinter as ctk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .logic import CatenaryLogic

from styles import DesignSystem


class CatenaryGUI(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, **DesignSystem.get_frame_style())
        self.controller = controller
        self.logic = CatenaryLogic()
        self.curve_data = None

        self.create_widgets()
        self.load_conductors()

    def create_widgets(self):
        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Cálculo de Catenária (Mecânico)",
            font=DesignSystem.FONT_SUBHEAD,
            text_color=DesignSystem.TEXT_MAIN,
        )
        self.header.pack(pady=20)

        # Main Layout: Controls (Left) and Plot (Right)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Controls Panel ---
        self.controls_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="#F8FAFC",
            corner_radius=15,
            border_width=1,
            border_color="#E2E8F0",
            width=300,
        )
        self.controls_frame.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(
            self.controls_frame, text="Parâmetros", font=DesignSystem.FONT_BODY, text_color=DesignSystem.TEXT_DIM
        ).pack(pady=10)

        # Conductor Selection
        ctk.CTkLabel(
            self.controls_frame, text="Condutor:", font=DesignSystem.FONT_BODY, text_color=DesignSystem.TEXT_MAIN
        ).pack(anchor="w", padx=15)
        self.cmb_conductor = ctk.CTkComboBox(
            self.controls_frame,
            values=["Carregando..."],
            command=self.on_conductor_change,
            **DesignSystem.get_entry_style(),
        )
        self.cmb_conductor.pack(fill="x", padx=15, pady=5)

        # Numeric Inputs
        self.inputs = {}
        for label, key in [
            ("Vão (m)", "span"),
            ("Altura A (m)", "ha"),
            ("Altura B (m)", "hb"),
            ("Tração (daN)", "tension"),
        ]:
            ctk.CTkLabel(
                self.controls_frame, text=label, font=DesignSystem.FONT_BODY, text_color=DesignSystem.TEXT_MAIN
            ).pack(anchor="w", padx=15)
            entry = ctk.CTkEntry(self.controls_frame, **DesignSystem.get_entry_style())
            entry.pack(fill="x", padx=15, pady=5)
            self.inputs[key] = entry

        # Default values
        self.inputs["span"].insert(0, "100")
        self.inputs["ha"].insert(0, "10")
        self.inputs["hb"].insert(0, "10")
        self.inputs["tension"].insert(0, "1000")

        # Action Buttons
        self.btn_calc = ctk.CTkButton(
            self.controls_frame, text="Calcular", command=self.calculate, **DesignSystem.get_button_style("primary")
        )
        self.btn_calc.pack(pady=15, padx=15, fill="x")

        self.lbl_result = ctk.CTkLabel(
            self.controls_frame, text="Flecha: -", font=DesignSystem.FONT_BODY, text_color=DesignSystem.TEXT_DIM
        )
        self.lbl_result.pack(pady=5)

        self.btn_dxf = ctk.CTkButton(
            self.controls_frame,
            text="Exportar DXF",
            command=self.export_dxf,
            state="disabled",
            **DesignSystem.get_button_style("secondary"),
        )
        self.btn_dxf.pack(pady=10, padx=15, fill="x")

        self.btn_back = ctk.CTkButton(
            self.controls_frame,
            text="Menu",
            command=lambda: self.controller.show_frame("Menu"),
            **DesignSystem.get_button_style("gray"),
        )
        self.btn_back.pack(side="bottom", pady=20, padx=15, fill="x")

        # --- Plot Panel ---
        self.plot_panel = ctk.CTkFrame(
            self.main_container, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0"
        )
        self.plot_panel.pack(side="right", fill="both", expand=True)

        self.fig, self.ax = plt.subplots(figsize=(5, 4), facecolor="white")
        self.ax.set_facecolor("#F8FAFC")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def load_conductors(self):
        names = self.logic.get_conductor_names()
        if names:
            self.cmb_conductor.configure(values=names)
            self.cmb_conductor.set(names[0])
            self.on_conductor_change(names[0])
        else:
            self.cmb_conductor.configure(values=["Nenhum condutor encontrado"])

    def on_conductor_change(self, choice):
        data = self.logic.get_conductor_by_name(choice)
        if data:
            # Update tension entry with default T0 if available
            self.inputs["tension"].delete(0, "end")
            self.inputs["tension"].insert(0, str(data.get("T0_daN", 1000)))

    def calculate(self):
        try:
            span = float(self.inputs["span"].get())
            ha = float(self.inputs["ha"].get())
            hb = float(self.inputs["hb"].get())
            tension = float(self.inputs["tension"].get())

            conductor_name = self.cmb_conductor.get()
            conductor_data = self.logic.get_conductor_by_name(conductor_name)

            if not conductor_data:
                messagebox.showerror("Erro", "Selecione um condutor válido.")
                return

            weight = conductor_data["P_kg_m"]

            result = self.logic.calculate_catenary(span, ha, hb, tension, weight)

            if result:
                self.curve_data = result
                self.lbl_result.configure(text=f"Flecha: {result['sag']:.2f} m")
                self.plot(result)
                # Share context with AI
                self.controller.project_context["catenary"] = result
                self.btn_dxf.configure(state="normal")
            else:
                messagebox.showerror("Erro", "Cálculo falhou.")

        except ValueError:
            messagebox.showerror("Erro", "Verifique se todos os campos numéricos estão corretos.")

    def plot(self, data):
        self.ax.clear()
        self.ax.plot(data["x_vals"], data["y_vals"], label="Catenária")
        self.ax.scatter(
            [0, data["x_vals"][-1]], [data["y_vals"][0], data["y_vals"][-1]], color="red", label="Suportes"
        )  # Supports
        self.ax.set_title(f"Catenária (Flecha: {data['sag']:.2f}m)")
        self.ax.set_xlabel("Distância (m)")
        self.ax.set_ylabel("Altura (m)")
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()

    def export_dxf(self):
        if not self.curve_data:
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("AutoCAD DXF", "*.dxf")])
        if not filepath:
            return

        try:
            self.logic.export_dxf(
                filepath, self.curve_data["x_vals"], self.curve_data["y_vals"], self.curve_data["sag"]
            )
            messagebox.showinfo("Sucesso", "DXF exportado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")
