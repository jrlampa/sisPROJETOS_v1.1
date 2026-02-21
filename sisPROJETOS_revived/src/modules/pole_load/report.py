import datetime
from typing import Any, Dict, List

from fpdf import FPDF


class PoleLoadReport(FPDF):
    def header(self) -> None:
        # Logo placeholder or Title
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "sisPROJETOS - Relatório de Cálculo de Esforço", border=False, align="C", ln=1)
        self.set_font("helvetica", "I", 10)
        self.cell(
            0, 10, f'Gerado em: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}', border=False, align="R", ln=1
        )
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")


def _build_pdf(data: List[Dict[str, Any]], result: Dict[str, Any], project_name: str) -> PoleLoadReport:
    """Constrói o objeto PDF de relatório de esforços sem gravá-lo em disco.

    Args:
        data: Lista de dicionários de cabos com chaves (rede, condutor, vao, angulo).
        result: Resultado de calculate_resultant (resultant_force, resultant_angle, vectors).
        project_name: Nome do projeto para o cabeçalho do relatório.

    Returns:
        Objeto PoleLoadReport pronto para salvar em disco ou em buffer.
    """
    pdf = PoleLoadReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Project Info
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, f"Projeto: {project_name}", ln=True)
    pdf.ln(5)

    # Input Data Table
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 10, "Dados de Entrada (Condutores):", ln=True)
    pdf.set_font("helvetica", "", 9)

    # Table Header
    cols = [("Rede", 35), ("Condutor", 70), ("Vão (m)", 20), ("Ângulo (°)", 25), ("Tração (daN)", 30)]
    for col, width in cols:
        pdf.cell(width, 8, col, border=1, align="C")
    pdf.ln()

    # Table Content
    for i, cable in enumerate(data):
        # Get tracao from results indices to be accurate
        tracao = result["vectors"][i]["tracao"]
        pdf.cell(cols[0][1], 8, str(cable["rede"]), border=1)
        pdf.cell(cols[1][1], 8, str(cable["condutor"]), border=1)
        pdf.cell(cols[2][1], 8, f"{cable['vao']:.1f}", border=1, align="C")
        pdf.cell(cols[3][1], 8, f"{cable['angulo']:.1f}", border=1, align="C")
        pdf.cell(cols[4][1], 8, f"{tracao:.2f}", border=1, align="C")
        pdf.ln()

    pdf.ln(10)

    # Results Section
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Resultados do Cálculo:", ln=True)
    pdf.set_font("helvetica", "", 11)

    pdf.cell(0, 8, f"Força Resultante Total: {result['resultant_force']:.2f} daN", ln=True)
    pdf.cell(0, 8, f"Ângulo da Resultante: {result['resultant_angle']:.2f} graus", ln=True)

    pdf.ln(10)
    pdf.set_font("helvetica", "I", 9)
    pdf.multi_cell(
        0,
        8,
        "Nota: Este relatório é um documento auxiliar de engenharia. "
        "A escolha final da estrutura deve respeitar os critérios de segurança da concessionária local "
        "e as condições de carga (Vento, Temperatura, etc).",
    )

    return pdf


def generate_report(
    filepath: str, data: List[Dict[str, Any]], result: Dict[str, Any], project_name: str = "N/A"
) -> None:
    """Gera o relatório PDF de esforços em postes e salva em disco.

    Args:
        filepath: Caminho completo para salvar o arquivo PDF.
        data: Lista de dicionários de cabos com chaves (rede, condutor, vao, angulo).
        result: Resultado de calculate_resultant (resultant_force, resultant_angle, vectors).
        project_name: Nome do projeto para o cabeçalho do relatório.
    """
    pdf = _build_pdf(data, result, project_name)
    pdf.output(filepath)


def generate_report_to_buffer(data: List[Dict[str, Any]], result: Dict[str, Any], project_name: str = "N/A") -> bytes:
    """Gera o relatório PDF de esforços em postes e retorna como bytes em memória.

    Não grava nenhum arquivo em disco. Útil para integração via API REST
    (retorno como Base64 JSON, conforme padrão /catenary/dxf).

    Args:
        data: Lista de dicionários de cabos com chaves (rede, condutor, vao, angulo).
        result: Resultado de calculate_resultant (resultant_force, resultant_angle, vectors).
        project_name: Nome do projeto para o cabeçalho do relatório.

    Returns:
        Conteúdo PDF em bytes prontos para codificação Base64.
    """
    pdf = _build_pdf(data, result, project_name)
    return bytes(pdf.output())
