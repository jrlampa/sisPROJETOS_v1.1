import customtkinter as ctk
from tkinter import filedialog, messagebox
from .logic import ConverterLogic
import os
import tkintermapview

from styles import DesignSystem


class ConverterGUI(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, **DesignSystem.get_frame_style())
        self.controller = controller
        self.logic = ConverterLogic()
        self.placemarks = []
        self.df = None
        self.marker_list = []

        self.create_widgets()

    def create_widgets(self):
        # Layout: Control Panel (Left), Map View (Right)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar / Controls ---
        self.side_panel = ctk.CTkFrame(
            self, width=320, fg_color="#F8FAFC", corner_radius=15, border_width=1, border_color="#E2E8F0"
        )
        self.side_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            self.side_panel,
            text="Conversor Geoespacial",
            font=DesignSystem.FONT_SUBHEAD,
            text_color=DesignSystem.TEXT_MAIN,
        ).pack(pady=30)

        self.btn_load = ctk.CTkButton(
            self.side_panel,
            text="Carregar KML/KMZ",
            command=self.load_file,
            **DesignSystem.get_button_style("primary"),
        )
        self.btn_load.pack(pady=10, padx=30, fill="x")

        self.lbl_file = ctk.CTkLabel(
            self.side_panel,
            text="Nenhum arquivo ativo",
            font=DesignSystem.FONT_BODY,
            text_color=DesignSystem.TEXT_DIM,
            wraplength=250,
        )
        self.lbl_file.pack(pady=5)

        self.status_frame = ctk.CTkFrame(self.side_panel, fg_color="white", corner_radius=10, height=40)
        self.status_frame.pack(pady=20, padx=30, fill="x")
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Aguardando...", font=DesignSystem.FONT_BODY)
        self.lbl_status.pack(expand=True)

        # Export Actions
        self.export_frame = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        self.export_frame.pack(pady=10, padx=30, fill="x")

        self.btn_export_excel = ctk.CTkButton(
            self.export_frame,
            text="Excel (.xlsx)",
            command=self.export_excel,
            state="disabled",
            **DesignSystem.get_button_style("secondary"),
        )
        self.btn_export_excel.pack(pady=5, fill="x")

        self.btn_export_csv = ctk.CTkButton(
            self.export_frame,
            text="CSV (.csv)",
            command=self.export_csv,
            state="disabled",
            **DesignSystem.get_button_style("secondary"),
        )
        self.btn_export_csv.pack(pady=5, fill="x")

        self.btn_export_dxf = ctk.CTkButton(
            self.export_frame,
            text="AutoCAD (.dxf)",
            command=self.export_dxf,
            state="disabled",
            **DesignSystem.get_button_style("purple"),
        )
        self.btn_export_dxf.pack(pady=5, fill="x")

        self.btn_back = ctk.CTkButton(
            self.side_panel,
            text="Voltar ao Menu",
            command=lambda: self.controller.show_frame("Menu"),
            **DesignSystem.get_button_style("gray"),
        )
        self.btn_back.pack(pady=30, side="bottom", padx=30, fill="x")

        # --- Map Panel ---
        self.map_container = ctk.CTkFrame(
            self, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0"
        )
        self.map_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.map_widget = tkintermapview.TkinterMapView(self.map_container, corner_radius=15)
        self.map_widget.pack(fill="both", expand=True, padx=2, pady=2)
        self.map_widget.set_position(-15.7801, -47.9292)  # Center on Brasilia
        self.map_widget.set_zoom(4)

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Google Earth Files", "*.kmz *.kml")])
        if not filepath:
            return

        self.lbl_file.configure(text=os.path.basename(filepath))
        self.lbl_status.configure(text="Processando...")
        self.update_idletasks()

        try:
            self.placemarks = self.logic.load_file(filepath)
            self.df = self.logic.convert_to_utm(self.placemarks)

            # Update Map
            self.map_widget.delete_all_marker()
            self.marker_list = []

            for p in self.placemarks:
                # p is a kml.Placemark object
                if hasattr(p.geometry, "x"):  # Point
                    marker = self.map_widget.set_marker(p.geometry.y, p.geometry.x, text=p.name)
                    self.marker_list.append(marker)
                elif hasattr(p.geometry, "coords"):  # LineString/Polygon
                    for lon, lat, *z in p.geometry.coords:
                        marker = self.map_widget.set_marker(lat, lon, text=p.name)
                        self.marker_list.append(marker)

            if self.placemarks:
                first_p = self.placemarks[0]
                if hasattr(first_p.geometry, "x"):
                    self.map_widget.set_position(first_p.geometry.y, first_p.geometry.x)
                elif hasattr(first_p.geometry, "coords"):
                    self.map_widget.set_position(first_p.geometry.coords[0][1], first_p.geometry.coords[0][0])
                self.map_widget.set_zoom(15)

            # Count unique features (placemarks), not vertices
            unique_features = len(self.df["Name"].unique()) if "Name" in self.df.columns and not self.df.empty else 0
            total_vertices = len(self.df)

            # Display appropriate message
            if unique_features == total_vertices:
                # All points (no lines)
                self.lbl_status.configure(text=f"Sucesso! {unique_features} ponto(s).", text_color="green")
            else:
                # Has lines with multiple vertices
                self.lbl_status.configure(
                    text=f"Sucesso! {unique_features} feature(s), {total_vertices} vértice(s).", text_color="green"
                )

            self.btn_export_excel.configure(state="normal")
            self.btn_export_csv.configure(state="normal")
            self.btn_export_dxf.configure(state="normal")

        except Exception as e:
            self.lbl_status.configure(text=f"Erro: {str(e)}")
            messagebox.showerror("Erro", str(e))

    def export_excel(self):
        if self.df is None or self.df.empty:
            messagebox.showwarning("Aviso", "Nenhum dado carregado. Por favor, abra um arquivo KML/KMZ primeiro.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if not filepath:
            return

        try:
            self.logic.save_to_excel(self.df, filepath)
            messagebox.showinfo("Sucesso", "Arquivo Excel salvo com sucesso!")
        except Exception as e:
            messagebox.showerror(
                "Erro ao salvar Excel",
                f"Erro: {str(e)}\n\nVerifique se o arquivo foi carregado e convertido corretamente.",
            )

    def export_csv(self):
        if self.df is None or self.df.empty:
            messagebox.showwarning("Aviso", "Nenhum dado carregado. Por favor, abra um arquivo KML/KMZ primeiro.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not filepath:
            return

        try:
            self.logic.save_to_csv(self.df, filepath)
            messagebox.showinfo("Sucesso", "Arquivo CSV salvo com sucesso!")
        except Exception as e:
            messagebox.showerror(
                "Erro ao salvar CSV",
                f"Erro: {str(e)}\n\nVerifique se o arquivo foi carregado e convertido corretamente.",
            )

    def export_dxf(self):
        if self.df is None or self.df.empty:
            messagebox.showwarning("Aviso", "Nenhum dado carregado. Por favor, abra um arquivo KML/KMZ primeiro.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("AutoCAD DXF", "*.dxf")])
        if not filepath:
            return

        try:
            self.logic.save_to_dxf(self.df, filepath)
            messagebox.showinfo("Sucesso", "Arquivo DXF salvo com sucesso!")
        except Exception as e:
            messagebox.showerror(
                "Erro ao salvar DXF",
                f"Erro: {str(e)}\n\nVerifique se o arquivo foi carregado e convertido corretamente.",
            )
