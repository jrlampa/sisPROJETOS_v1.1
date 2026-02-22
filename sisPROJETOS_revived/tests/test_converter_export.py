"""
Testes de exportação do módulo converter — separados para manter
test_converter_edge_cases.py abaixo do limite de 500 linhas.

Cobre: save_to_csv, save_to_excel, save_to_dxf e save_to_dxf_to_buffer
(validação de extensão via sanitizer + comportamento correto de buffer DXF).
"""

import io
import zipfile

import ezdxf
import pandas as pd
import pytest

from src.modules.converter.logic import ConverterLogic

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def converter():
    return ConverterLogic()


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        [
            {
                "Name": "P1",
                "Easting": 788547.0,
                "Northing": 7634925.0,
                "Zone": 23,
                "Longitude": -43.5,
                "Latitude": -21.5,
                "Elevation": 720.0,
                "Description": "Ponto 1",
                "Hemisphere": "S",
                "Type": "Point",
            }
        ]
    )


# ── TestConverterCSVExportEdgeCases ──────────────────────────────────────────


class TestConverterCSVExportEdgeCases:
    """Cobertura de edge cases na exportação CSV."""

    def test_save_csv_to_invalid_path_raises_value_error(self, converter, sample_df):
        """Linha 353-354: exceção ao salvar CSV em caminho inválido."""
        with pytest.raises(ValueError, match="Error saving CSV file"):
            converter.save_to_csv(sample_df, "/diretorio/inexistente/arquivo.csv")

    def test_save_to_excel_invalid_extension_raises(self, converter, sample_df):
        """Sanitizer: save_to_excel com extensão errada deve lançar ValueError."""
        with pytest.raises(ValueError, match="Extensão"):
            converter.save_to_excel(sample_df, "/tmp/arquivo.csv")

    def test_save_to_dxf_invalid_extension_raises(self, converter, sample_df):
        """Sanitizer: save_to_dxf com extensão errada deve lançar ValueError."""
        with pytest.raises(ValueError, match="Extensão"):
            converter.save_to_dxf(sample_df, "/tmp/arquivo.txt")

    def test_save_to_csv_invalid_extension_raises(self, converter, sample_df):
        """Sanitizer: save_to_csv com extensão errada deve lançar ValueError."""
        with pytest.raises(ValueError, match="Extensão"):
            converter.save_to_csv(sample_df, "/tmp/arquivo.xlsx")


# ── TestConverterDxfToBuffer ─────────────────────────────────────────────────


class TestConverterDxfToBuffer:
    """Testes para ConverterLogic.save_to_dxf_to_buffer() — todos os branches."""

    def test_retorna_bytes_valido(self, converter, sample_df):
        """save_to_dxf_to_buffer retorna bytes não-vazios com conteúdo DXF."""
        result = converter.save_to_dxf_to_buffer(sample_df)
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert b"SECTION" in result

    def test_dataframe_vazio_levanta_value_error(self, converter):
        """Linha 381: DataFrame vazio deve lançar ValueError."""
        with pytest.raises(ValueError, match="DataFrame vazio"):
            converter.save_to_dxf_to_buffer(pd.DataFrame())

    def test_colunas_faltando_levanta_value_error(self, converter):
        """Linha 386: DataFrame sem coluna obrigatória deve lançar ValueError."""
        df_incompleto = pd.DataFrame({"Name": ["P1"], "Easting": [788547.0]})
        with pytest.raises(ValueError, match="Colunas necessárias faltando"):
            converter.save_to_dxf_to_buffer(df_incompleto)

    def test_multiplos_pontos_mesmo_nome_geram_polilinha(self, converter):
        """Linhas 402-407: Dois pontos com mesmo nome devem gerar layer LINES."""
        df = pd.DataFrame(
            {
                "Name": ["LINHA1", "LINHA1"],
                "Easting": [788547.0, 788647.0],
                "Northing": [7634925.0, 7635025.0],
                "Elevation": [720.0, 721.0],
            }
        )
        result = converter.save_to_dxf_to_buffer(df)
        doc = ezdxf.read(io.StringIO(result.decode("utf-8")))
        msp = doc.modelspace()
        lines_entities = [e for e in msp if e.dxf.layer == "LINES"]
        assert len(lines_entities) > 0
