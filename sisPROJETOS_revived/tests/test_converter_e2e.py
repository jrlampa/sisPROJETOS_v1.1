"""
Teste End-to-End do Conversor KMZ/KML.

Valida o fluxo completo de conversão:
KML → DataFrame → XLSX/CSV/DXF
"""

import os
import tempfile

import pandas as pd
import pytest

from src.modules.converter.logic import ConverterLogic


class TestConverterE2E:
    """Suite de testes end-to-end para o conversor KML."""

    @pytest.fixture
    def converter(self):
        """Fixture que retorna uma instância de ConverterLogic."""
        return ConverterLogic()

    @pytest.fixture
    def test_kml_path(self):
        """Retorna o caminho para o arquivo KML de teste."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "fixtures", "test_project.kml")

    def test_kml_file_exists(self, test_kml_path):
        """Verifica que o arquivo KML de teste existe."""
        assert os.path.exists(test_kml_path), f"Arquivo KML de teste não encontrado: {test_kml_path}"
        assert os.path.getsize(test_kml_path) > 0, "Arquivo KML de teste está vazio"

    def test_load_kml_file(self, converter, test_kml_path):
        """Testa carregamento do arquivo KML."""
        placemarks = converter.load_file(test_kml_path)

        # Validações
        assert placemarks is not None, "load_file retornou None"
        assert len(placemarks) > 0, "Nenhum placemark foi extraído"
        assert len(placemarks) == 6, f"Esperado 6 placemarks, encontrados {len(placemarks)}"

        # Verificar nomes dos placemarks
        names = [p.name for p in placemarks]
        assert "Poste P1" in names, "Placemark 'Poste P1' não encontrado"
        assert "Rede Primária R1" in names, "Placemark 'Rede Primária R1' não encontrado"
        assert "Área do Projeto" in names, "Placemark 'Área do Projeto' não encontrado"

    def test_convert_to_utm(self, converter, test_kml_path):
        """Testa conversão de coordenadas para UTM."""
        placemarks = converter.load_file(test_kml_path)
        df = converter.convert_to_utm(placemarks)

        # Validações do DataFrame
        assert df is not None, "convert_to_utm retornou None"
        assert not df.empty, "DataFrame está vazio"
        assert len(df) > 0, "DataFrame não tem linhas"

        # Verificar colunas obrigatórias
        required_cols = [
            "Name",
            "Description",
            "Type",
            "Longitude",
            "Latitude",
            "Easting",
            "Northing",
            "Zone",
            "Hemisphere",
            "Elevation",
        ]
        for col in required_cols:
            assert col in df.columns, f"Coluna '{col}' não encontrada no DataFrame"

        # Verificar tipos de geometria
        assert "Point" in df["Type"].values, "Nenhum Point encontrado"
        assert "LineString" in df["Type"].values, "Nenhum LineString encontrado"
        # Polygon pode ter sido convertido para LineString (apenas exterior ring)

        # Verificar zona UTM (São Paulo é zona 23S)
        assert all(df["Zone"] == 23), "Zona UTM incorreta (esperado 23 para São Paulo)"
        assert all(df["Hemisphere"] == "S"), "Hemisfério incorreto (esperado 'S')"

        # Verificar que coordenadas UTM estão razoáveis
        assert all(df["Easting"] > 0), "Easting deve ser positivo"
        assert all(df["Northing"] > 0), "Northing deve ser positivo"
        assert all(df["Easting"] > 300000), "Easting fora do range esperado para zona 23"
        assert all(df["Easting"] < 400000), "Easting fora do range esperado para zona 23"

    def test_export_to_xlsx(self, converter, test_kml_path):
        """Testa exportação completa para XLSX."""
        placemarks = converter.load_file(test_kml_path)
        df = converter.convert_to_utm(placemarks)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            try:
                # Exportar
                converter.save_to_excel(df, tmp.name)

                # Validar arquivo
                assert os.path.exists(tmp.name), "Arquivo XLSX não foi criado"
                assert os.path.getsize(tmp.name) > 0, "Arquivo XLSX está vazio"
                assert (
                    os.path.getsize(tmp.name) > 1000
                ), f"Arquivo XLSX muito pequeno: {os.path.getsize(tmp.name)} bytes"

                # Verificar que pode ser lido
                df_loaded = pd.read_excel(tmp.name)
                assert len(df_loaded) == len(df), "Número de linhas diferente após reload"
                assert list(df_loaded.columns) == list(df.columns), "Colunas diferentes após reload"

            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

    def test_export_to_csv(self, converter, test_kml_path):
        """Testa exportação completa para CSV."""
        placemarks = converter.load_file(test_kml_path)
        df = converter.convert_to_utm(placemarks)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8-sig") as tmp:
            try:
                # Exportar
                converter.save_to_csv(df, tmp.name)

                # Validar arquivo
                assert os.path.exists(tmp.name), "Arquivo CSV não foi criado"
                assert os.path.getsize(tmp.name) > 0, "Arquivo CSV está vazio"

                # Verificar conteúdo
                with open(tmp.name, "r", encoding="utf-8-sig") as f:
                    content = f.read()

                    # Verificar separador
                    first_line = content.split("\n")[0]
                    assert ";" in first_line, "Separador ';' não encontrado no cabeçalho CSV"

                    # Verificar que tem dados
                    lines = content.strip().split("\n")
                    assert len(lines) > 1, "CSV não tem linhas de dados"

                # Verificar que pode ser lido
                df_loaded = pd.read_csv(tmp.name, sep=";", encoding="utf-8-sig")
                assert len(df_loaded) == len(df), "Número de linhas diferente após reload"

            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

    def test_export_to_dxf(self, converter, test_kml_path):
        """Testa exportação completa para DXF."""
        placemarks = converter.load_file(test_kml_path)
        df = converter.convert_to_utm(placemarks)

        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
            try:
                # Exportar
                converter.save_to_dxf(df, tmp.name)

                # Validar arquivo
                assert os.path.exists(tmp.name), "Arquivo DXF não foi criado"
                assert os.path.getsize(tmp.name) > 0, "Arquivo DXF está vazio"
                assert (
                    os.path.getsize(tmp.name) > 5000
                ), f"Arquivo DXF muito pequeno: {os.path.getsize(tmp.name)} bytes"

                # Verificar conteúdo básico
                with open(tmp.name, "r") as f:
                    content = f.read()

                    # Verificar estrutura DXF
                    assert "SECTION" in content, "Estrutura DXF: SECTION não encontrada"
                    assert "ENTITIES" in content, "Estrutura DXF: ENTITIES não encontrada"
                    assert "POINT" in content or "POLYLINE" in content, "Nenhuma entidade geométrica encontrada no DXF"

                    # Verificar layers
                    assert "POINTS" in content or "LINES" in content, "Layers esperados não encontrados no DXF"

            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

    def test_full_pipeline(self, converter, test_kml_path):
        """Teste completo do pipeline: KML → DataFrame → Todos os formatos."""
        # Passo 1: Carregar KML
        placemarks = converter.load_file(test_kml_path)
        assert len(placemarks) == 6, "Carregamento KML falhou"

        # Passo 2: Converter para UTM
        df = converter.convert_to_utm(placemarks)
        assert not df.empty, "Conversão para UTM falhou"
        assert len(df) >= 6, f"Conversão gerou menos linhas que esperado: {len(df)}"

        # Passo 3: Exportar para todos os formatos
        with tempfile.TemporaryDirectory() as tmpdir:
            xlsx_path = os.path.join(tmpdir, "output.xlsx")
            csv_path = os.path.join(tmpdir, "output.csv")
            dxf_path = os.path.join(tmpdir, "output.dxf")

            # Exportar
            converter.save_to_excel(df, xlsx_path)
            converter.save_to_csv(df, csv_path)
            converter.save_to_dxf(df, dxf_path)

            # Validar que todos foram criados
            assert os.path.exists(xlsx_path), "XLSX não foi criado no pipeline completo"
            assert os.path.exists(csv_path), "CSV não foi criado no pipeline completo"
            assert os.path.exists(dxf_path), "DXF não foi criado no pipeline completo"

            # Validar tamanhos
            assert os.path.getsize(xlsx_path) > 1000, "XLSX muito pequeno"
            assert os.path.getsize(csv_path) > 100, "CSV muito pequeno"
            assert os.path.getsize(dxf_path) > 5000, "DXF muito pequeno"

    def test_data_integrity(self, converter, test_kml_path):
        """Testa integridade dos dados durante a conversão."""
        placemarks = converter.load_file(test_kml_path)
        df = converter.convert_to_utm(placemarks)

        # Verificar que nomes foram preservados
        assert "Poste P1" in df["Name"].values, "Nome 'Poste P1' não preservado"
        assert "Poste P2" in df["Name"].values, "Nome 'Poste P2' não preservado"
        assert "Transformador T1" in df["Name"].values, "Nome 'Transformador T1' não preservado"

        # Verificar que descrições foram preservadas
        assert any("concreto" in str(d).lower() for d in df["Description"].values), "Descrições não preservadas"

        # Verificar elevações
        assert any(df["Elevation"] == 720), "Elevação 720m não encontrada"
        assert any(df["Elevation"] == 722), "Elevação 722m não encontrada"
        assert any(df["Elevation"] == 725), "Elevação 725m não encontrada"

        # Verificar que coordenadas são consistentes
        # Poste P1 deve estar em aproximadamente (-46.6333, -23.5505)
        p1_rows = df[df["Name"] == "Poste P1"]
        assert len(p1_rows) == 1, "Poste P1 deve aparecer exatamente uma vez"
        p1 = p1_rows.iloc[0]
        assert abs(p1["Longitude"] - (-46.6333)) < 0.001, "Longitude do Poste P1 incorreta"
        assert abs(p1["Latitude"] - (-23.5505)) < 0.001, "Latitude do Poste P1 incorreta"
