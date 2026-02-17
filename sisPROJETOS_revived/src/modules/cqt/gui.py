import customtkinter as ctk
from tkinter import messagebox, filedialog
from .logic import CQTLogic
import pandas as pd

from styles import DesignSystem


class CQTGUI(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, **DesignSystem.get_frame_style())
        self.controller = controller
        self.logic = CQTLogic()
        self.rows = []

        self.create_widgets()
        self.add_row(["TRAFO", "", "0", "", "0", "0", "0", "0", "0"])

    def create_widgets(self):
        # Header Area
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            self.header_frame,
            text="CQT / QTOS (Análise Radial)",
            font=DesignSystem.FONT_SUBHEAD,
            text_color=DesignSystem.TEXT_MAIN,
        ).pack(side="left")

        # Global Settings Frame
        self.settings_bar = ctk.CTkFrame(
            self, fg_color="#F8FAFC", corner_radius=12, border_width=1, border_color="#E2E8F0"
        )
        self.settings_bar.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(self.settings_bar, text="Trafo (kVA):", font=DesignSystem.FONT_BODY).pack(
            side="left", padx=(15, 5), pady=10
        )
        self.ent_trafo_kva = ctk.CTkEntry(self.settings_bar, width=80, **DesignSystem.get_entry_style())
        self.ent_trafo_kva.insert(0, "75")
        self.ent_trafo_kva.pack(side="left", padx=5)

        ctk.CTkLabel(self.settings_bar, text="Classe:", font=DesignSystem.FONT_BODY).pack(side="left", padx=(15, 5))
        self.cmb_class = ctk.CTkComboBox(
            self.settings_bar, values=["A", "B", "C", "D"], width=80, **DesignSystem.get_entry_style()
        )
        self.cmb_class.set("B")
        self.cmb_class.pack(side="left", padx=5)

        # Action Buttons
        self.btn_calc = ctk.CTkButton(
            self.settings_bar,
            text="Calcular",
            width=100,
            command=self.calculate,
            **DesignSystem.get_button_style("primary"),
        )
        self.btn_calc.pack(side="right", padx=15)

        self.btn_add = ctk.CTkButton(
            self.settings_bar,
            text="+ Trecho",
            width=100,
            command=self.add_row,
            **DesignSystem.get_button_style("success"),
        )
        self.btn_add.pack(side="right", padx=5)

        # Table Area
        self.table_side = ctk.CTkFrame(
            self, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0"
        )
        self.table_side.pack(fill="both", expand=True, padx=20, pady=10)

        self.table_container = ctk.CTkScrollableFrame(self.table_side, fg_color="transparent")
        self.table_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Headers
        headers = ["PONTO", "MONTANTE", "METROS", "CABO", "MONO", "BI", "TRI", "TRI_ESP", "CARGA_ESP"]
        self.header_widths = [90, 90, 70, 140, 50, 50, 50, 60, 80]

        self.header_row = ctk.CTkFrame(self.table_container, fg_color="#F1F5F9", corner_radius=8)
        self.header_row.grid(row=0, column=0, columnspan=10, sticky="ew", pady=(0, 5))

        for i, (h, w) in enumerate(zip(headers, self.header_widths)):
            lbl = ctk.CTkLabel(
                self.header_row, text=h, font=DesignSystem.FONT_BODY, width=w, text_color=DesignSystem.TEXT_DIM
            )
            lbl.grid(row=0, column=i, padx=2, pady=5)

        # Footer Area
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", padx=20, pady=15)

        self.lbl_summary = ctk.CTkLabel(
            self.footer,
            text="Resumo: Aguardando cálculo...",
            font=DesignSystem.FONT_BODY,
            text_color=DesignSystem.TEXT_DIM,
        )
        self.lbl_summary.pack(side="left")

        self.btn_export = ctk.CTkButton(
            self.footer,
            text="Excel",
            width=100,
            command=self.export_excel,
            **DesignSystem.get_button_style("secondary"),
        )
        self.btn_export.pack(side="right", padx=5)

        self.btn_back = ctk.CTkButton(
            self.footer,
            text="Menu",
            width=100,
            command=lambda: self.controller.show_frame("Menu"),
            **DesignSystem.get_button_style("gray"),
        )
        self.btn_back.pack(side="right", padx=5)

    def add_row(self, values=None):
        row_idx = len(self.rows) + 1
        row_widgets = {}

        fields = ["ponto", "montante", "metros", "cabo", "mono", "bi", "tri", "tri_esp", "carga_esp"]
        # Standard cable choices for autocomplete/shortcut (placeholder for combo)
        cables = list(self.logic.CABOS_COEFS.keys())

        for i, (f, w) in enumerate(zip(fields, self.header_widths)):
            if f == "cabo":
                ent = ctk.CTkComboBox(self.table_container, values=cables, width=w)
            else:
                ent = ctk.CTkEntry(self.table_container, width=w)

            ent.grid(row=row_idx, column=i, padx=2, pady=2)

            if values and i < len(values):
                if f == "cabo":
                    ent.set(values[i])
                else:
                    ent.insert(0, values[i])

            row_widgets[f] = ent

        # Add Delete Button
        if row_idx > 1:  # Don't delete TRAFO
            btn_del = ctk.CTkButton(
                self.table_container,
                text="X",
                width=30,
                fg_color="red",
                command=lambda r=row_widgets: self.remove_row(r),
            )
            btn_del.grid(row=row_idx, column=len(fields), padx=5)
            row_widgets["btn_del"] = btn_del

        self.rows.append(row_widgets)

    def remove_row(self, row_widgets):
        for w in row_widgets.values():
            w.destroy()
        self.rows.remove(row_widgets)

    def get_data(self):
        data = []
        for r in self.rows:
            try:
                row_data = {
                    "ponto": r["ponto"].get().strip(),
                    "montante": r["montante"].get().strip(),
                    "metros": float(r["metros"].get() or 0),
                    "cabo": r["cabo"].get().strip(),
                    "mono": int(r["mono"].get() or 0),
                    "bi": int(r["bi"].get() or 0),
                    "tri": int(r["tri"].get() or 0),
                    "tri_esp": int(r["tri_esp"].get() or 0),
                    "carga_esp": float(r["carga_esp"].get() or 0),
                }
                if row_data["ponto"]:
                    data.append(row_data)
            except ValueError:
                continue
        return data

    def calculate(self):
        segments = self.get_data()
        trafo_kva = float(self.ent_trafo_kva.get() or 0)
        social_class = self.cmb_class.get()

        res = self.logic.calculate(segments, trafo_kva, social_class)

        if res["success"]:
            summary = res["summary"]
            txt = (
                f"CQT Máximo: {summary['max_cqt']:.2f}% | "
                f"Demanda Total: {summary['total_kva']:.1f} kVA | "
                f"Clientes: {summary['total_clients']} | "
                f"Fator: {summary['fd']:.2f}"
            )
            self.lbl_summary.configure(text=txt, text_color=DesignSystem.TEXT_MAIN)

            # Highlight bottlenecks in the table (color entries where CQT is high)
            for r in self.rows:
                p = r["ponto"].get().upper()
                if p in res["results"]:
                    cqt = res["results"][p]["cqt_accumulated"]
                    color = "red" if cqt > 5.0 else "white"  # ENEL uses 5 or 6 depending on case
                    r["ponto"].configure(text_color=color)

            # Share context for AI
            self.controller.project_context["cqt"] = res
            messagebox.showinfo("Sucesso", "Cálculo do CQT finalizado com sucesso!")
        else:
            messagebox.showerror("Erro no Cálculo", res["error"])

    def export_excel(self):
        data = self.get_data()
        if not data:
            messagebox.showwarning("Aviso", "Não há dados para exportar.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                df = pd.DataFrame(data)
                # If calculation was performed, we could enrich this with results
                if "cqt" in self.controller.project_context:
                    res = self.controller.project_context["cqt"]["results"]
                    df["CQT_Acumulado_%"] = df["ponto"].apply(
                        lambda x: res.get(x.upper(), {}).get("cqt_accumulated", 0)
                    )
                    df["Carga_Acumulada_kVA"] = df["ponto"].apply(
                        lambda x: res.get(x.upper(), {}).get("accumulated", 0)
                    )

                df.to_excel(file_path, index=False)
                messagebox.showinfo("Sucesso", f"Dados exportados para: {file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
