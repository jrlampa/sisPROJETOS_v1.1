from fpdf import FPDF
import datetime


class PoleLoadReport(FPDF):
    def header(self):
        # Logo placeholder or Title
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'sisPROJETOS - Relatório de Cálculo de Esforço', border=False, align='C', ln=1)
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 10, f'Gerado em: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}', border=False, align='R', ln=1)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C')

def generate_report(filepath, data, result, project_name="N/A"):
    """
    Generates a PDF report for Pole Load.
    
    Args:
        filepath (str): Path to save the PDF.
        data (list): Input cables data list.
        result (dict): result from calculate_resultant.
        project_name (str): Name of the project.
    """
    pdf = PoleLoadReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Project Info
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f'Projeto: {project_name}', ln=True)
    pdf.ln(5)
    
    # Input Data Table
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 10, 'Dados de Entrada (Condutores):', ln=True)
    pdf.set_font('helvetica', '', 9)
    
    # Table Header
    cols = [('Rede', 35), ('Condutor', 70), ('Vão (m)', 20), ('Ângulo (°)', 25), ('Tração (daN)', 30)]
    for col, width in cols:
        pdf.cell(width, 8, col, border=1, align='C')
    pdf.ln()
    
    # Table Content
    for i, cable in enumerate(data):
        # Get tracao from results indices to be accurate
        tracao = result['vectors'][i]['tracao']
        pdf.cell(cols[0][1], 8, str(cable['rede']), border=1)
        pdf.cell(cols[1][1], 8, str(cable['condutor']), border=1)
        pdf.cell(cols[2][1], 8, f"{cable['vao']:.1f}", border=1, align='C')
        pdf.cell(cols[3][1], 8, f"{cable['angulo']:.1f}", border=1, align='C')
        pdf.cell(cols[4][1], 8, f"{tracao:.2f}", border=1, align='C')
        pdf.ln()
    
    pdf.ln(10)
    
    # Results Section
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Resultados do Cálculo:', ln=True)
    pdf.set_font('helvetica', '', 11)
    
    pdf.cell(0, 8, f"Força Resultante Total: {result['resultant_force']:.2f} daN", ln=True)
    pdf.cell(0, 8, f"Ângulo da Resultante: {result['resultant_angle']:.2f} graus", ln=True)
    
    # Selection logic for "Poste Suporta?"
    # (Usually this logic is in the GUI/Logic, but we can summarize here)
    pdf.ln(10)
    pdf.set_font('helvetica', 'I', 9)
    pdf.multi_cell(0, 8, 
        "Nota: Este relatório é um documento auxiliar de engenharia. "
        "A escolha final da estrutura deve respeitar os critérios de segurança da concessionária local "
        "e as condições de carga (Vento, Temperatura, etc)."
    )
    
    pdf.output(filepath)
