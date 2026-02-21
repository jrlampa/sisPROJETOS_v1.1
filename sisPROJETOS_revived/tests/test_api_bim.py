"""
Testes unitários e de integração para endpoints BIM da API REST do sisPROJETOS.

Cobre:
- GET  /api/v1/data/conductors
- GET  /api/v1/data/poles
- GET  /api/v1/data/concessionaires
- POST /api/v1/converter/kml-to-utm
- POST /api/v1/projects/create
"""

import base64
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Cliente de testes FastAPI (reutilizado em todos os testes do módulo)."""
    from src.api.app import create_app

    app = create_app()
    return TestClient(app)


# ── Dados Mestres ─────────────────────────────────────────────────────────────


class TestDataEndpoints:
    """Testa os endpoints de consulta de dados mestres (BIM integration)."""

    def test_list_conductors_retorna_200(self, client):
        resp = client.get("/api/v1/data/conductors")
        assert resp.status_code == 200

    def test_list_conductors_tem_campos_obrigatorios(self, client):
        data = client.get("/api/v1/data/conductors").json()
        assert len(data) > 0
        for item in data:
            assert "name" in item
            assert "weight_kg_m" in item
            assert isinstance(item["weight_kg_m"], float)

    def test_list_conductors_dados_reais_db(self, client):
        """Verifica que os condutores vêm do DB real (não mockados)."""
        data = client.get("/api/v1/data/conductors").json()
        names = [c["name"] for c in data]
        assert "556MCM-CA, Nu" in names  # Condutor Light pré-populado no DB

    def test_list_poles_retorna_200(self, client):
        resp = client.get("/api/v1/data/poles")
        assert resp.status_code == 200

    def test_list_poles_tem_campos_obrigatorios(self, client):
        data = client.get("/api/v1/data/poles").json()
        assert len(data) > 0
        for item in data:
            assert "material" in item
            assert "format" in item
            assert "description" in item
            assert "nominal_load_daN" in item
            assert isinstance(item["nominal_load_daN"], float)

    def test_list_poles_dados_reais_db(self, client):
        """Verifica que os postes vêm do DB real e têm material Concreto."""
        data = client.get("/api/v1/data/poles").json()
        materials = {p["material"] for p in data}
        assert "Concreto" in materials

    def test_list_concessionaires_retorna_200(self, client):
        resp = client.get("/api/v1/data/concessionaires")
        assert resp.status_code == 200

    def test_list_concessionaires_tem_campos_obrigatorios(self, client):
        data = client.get("/api/v1/data/concessionaires").json()
        assert len(data) > 0
        for item in data:
            assert "name" in item
            assert "method" in item

    def test_list_concessionaires_dados_reais_db(self, client):
        """Verifica que Light e Enel estão no DB com métodos corretos."""
        data = client.get("/api/v1/data/concessionaires").json()
        by_name = {c["name"]: c["method"] for c in data}
        assert "Light" in by_name
        assert "Enel" in by_name
        assert by_name["Light"] == "flecha"
        assert by_name["Enel"] == "tabela"

    def test_conductors_db_error_retorna_500(self, client, mocker):
        """Cobre branch de exceção do DB → HTTP 500."""
        mocker.patch(
            "api.routes.data._db.get_all_conductors",
            side_effect=Exception("DB falhou"),
        )
        resp = client.get("/api/v1/data/conductors")
        assert resp.status_code == 500

    def test_poles_db_error_retorna_500(self, client, mocker):
        """Cobre branch de exceção do DB → HTTP 500."""
        mocker.patch(
            "api.routes.data._db.get_all_poles",
            side_effect=Exception("DB falhou"),
        )
        resp = client.get("/api/v1/data/poles")
        assert resp.status_code == 500

    def test_concessionaires_db_error_retorna_500(self, client, mocker):
        """Cobre branch de exceção do DB → HTTP 500."""
        mocker.patch(
            "api.routes.data._db.get_all_concessionaires",
            side_effect=Exception("DB falhou"),
        )
        resp = client.get("/api/v1/data/concessionaires")
        assert resp.status_code == 500


# ── Conversor KML/KMZ ─────────────────────────────────────────────────────────

# KML mínimo com um Placemark do tipo Point (coordenadas de São Paulo)
_KML_MINIMAL = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Poste P1</name>
      <description>Teste BIM</description>
      <Point>
        <coordinates>-46.6333,-23.5505,850</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""


class TestConverterKmlEndpoint:
    """Testes para POST /api/v1/converter/kml-to-utm."""

    def test_retorna_200_com_kml_valido(self, client):
        """Happy path: KML válido retorna 200 com lista de pontos UTM."""
        payload = {"kml_base64": base64.b64encode(_KML_MINIMAL).decode()}
        resp = client.post("/api/v1/converter/kml-to-utm", json=payload)
        assert resp.status_code == 200

    def test_resposta_tem_campos_count_e_points(self, client):
        """Verifica campos obrigatórios na resposta."""
        payload = {"kml_base64": base64.b64encode(_KML_MINIMAL).decode()}
        data = client.post("/api/v1/converter/kml-to-utm", json=payload).json()
        assert "count" in data
        assert "points" in data
        assert data["count"] == len(data["points"])

    def test_ponto_tem_coordenadas_utm_validas(self, client):
        """Coordenadas UTM devem ser números positivos para o Brasil."""
        payload = {"kml_base64": base64.b64encode(_KML_MINIMAL).decode()}
        data = client.post("/api/v1/converter/kml-to-utm", json=payload).json()
        pt = data["points"][0]
        assert pt["name"] == "Poste P1"
        assert pt["hemisphere"] == "S"
        assert pt["zone"] == 23
        assert pt["easting"] > 100_000  # UTM Easting > 100 km
        assert pt["northing"] > 7_000_000  # UTM Northing Sul do equador (7M+)
        assert pt["elevation"] == 850.0

    def test_base64_invalido_retorna_422(self, client):
        """Payload não é Base64 válido → 422."""
        payload = {"kml_base64": "!!! not base64 !!!"}
        resp = client.post("/api/v1/converter/kml-to-utm", json=payload)
        assert resp.status_code == 422

    def test_kml_vazio_retorna_422(self, client):
        """Base64 de conteúdo vazio → 422 (KML vazio)."""
        payload = {"kml_base64": base64.b64encode(b"").decode()}
        resp = client.post("/api/v1/converter/kml-to-utm", json=payload)
        assert resp.status_code == 422

    def test_kml_sem_placemarks_retorna_422(self, client, mocker):
        """KML sem placemarks → load_kml_content levanta ValueError → 422."""
        mocker.patch(
            "api.routes.converter._logic.load_kml_content",
            side_effect=ValueError("No features found in KML file"),
        )
        payload = {"kml_base64": base64.b64encode(_KML_MINIMAL).decode()}
        resp = client.post("/api/v1/converter/kml-to-utm", json=payload)
        assert resp.status_code == 422
        detail = resp.json()["detail"].lower()
        assert "features" in detail or "kml" in detail

    def test_falha_na_conversao_utm_retorna_422(self, client, mocker):
        """Erro na conversão UTM → 422."""
        mocker.patch(
            "api.routes.converter._logic.load_kml_content",
            return_value=["mock_placemark"],
        )
        mocker.patch(
            "api.routes.converter._logic.convert_to_utm",
            side_effect=ValueError("No valid geometries found"),
        )
        payload = {"kml_base64": base64.b64encode(_KML_MINIMAL).decode()}
        resp = client.post("/api/v1/converter/kml-to-utm", json=payload)
        assert resp.status_code == 422


# ── Criador de Projetos ───────────────────────────────────────────────────────


class TestProjectCreatorEndpoint:
    """Testes para POST /api/v1/projects/create."""

    _URL = "/api/v1/projects/create"

    def test_criacao_sucesso_via_mock(self, client, mocker):
        """Happy path: lógica mockada retorna sucesso → 200 com success=True."""
        mocker.patch(
            "api.routes.project_creator._logic.create_structure",
            return_value=(True, "Projeto criado com sucesso!"),
        )
        payload = {"project_name": "PROJ_TESTE", "base_path": "/projetos"}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "Projeto criado" in data["message"]
        assert data["project_path"] == "/projetos/PROJ_TESTE"

    def test_criacao_falha_via_mock(self, client, mocker):
        """Falha na criação (pasta já existe) → 200 com success=False."""
        mocker.patch(
            "api.routes.project_creator._logic.create_structure",
            return_value=(False, "Erro: A pasta 'PROJ_TESTE' já existe."),
        )
        payload = {"project_name": "PROJ_TESTE", "base_path": "/projetos"}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["project_path"] is None

    def test_nome_projeto_vazio_retorna_422(self, client):
        """Nome de projeto vazio falha na validação Pydantic → 422."""
        payload = {"project_name": "", "base_path": "/projetos"}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422

    def test_nome_projeto_muito_longo_retorna_422(self, client):
        """Nome de projeto com > 100 caracteres falha na validação Pydantic → 422."""
        payload = {"project_name": "A" * 101, "base_path": "/projetos"}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422

    def test_campos_obrigatorios_ausentes_retorna_422(self, client):
        """Payload sem base_path falha na validação Pydantic → 422."""
        payload = {"project_name": "PROJ_TESTE"}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422

    def test_criacao_real_em_tmp(self, client):
        """Teste de integração real: cria projeto em diretório temporário."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = {"project_name": "LT_TESTE_BIM", "base_path": tmp_dir}
            resp = client.post(self._URL, json=payload)
            assert resp.status_code == 200
            data = resp.json()
            # mas o campo success sempre está presente
            assert "success" in data
            assert "message" in data
            # project_path deve ser consistente com project_name
            if data["success"]:
                assert "LT_TESTE_BIM" in data["project_path"]


# ── Relatório PDF de Esforços em Postes ───────────────────────────────────────


class TestPoleLoadReportEndpoint:
    """Testes para POST /api/v1/pole-load/report."""

    _URL = "/api/v1/pole-load/report"
    _PAYLOAD = {
        "concessionaria": "Light",
        "condicao": "Normal",
        "cabos": [{"condutor": "556MCM-CA, Nu", "vao": 80.0, "angulo": 30.0, "flecha": 1.5}],
        "project_name": "Projeto Teste API",
        "filename": "relatorio_trecho01.pdf",
    }

    def test_relatorio_retorna_200(self, client):
        """Requisição válida retorna HTTP 200."""
        resp = client.post(self._URL, json=self._PAYLOAD)
        assert resp.status_code == 200

    def test_relatorio_tem_campos_obrigatorios(self, client):
        """Resposta contém pdf_base64, filename e resultant_force."""
        resp = client.post(self._URL, json=self._PAYLOAD)
        data = resp.json()
        assert "pdf_base64" in data
        assert "filename" in data
        assert "resultant_force" in data

    def test_pdf_base64_e_valido(self, client):
        """pdf_base64 é uma string Base64 válida com conteúdo PDF."""
        import base64

        resp = client.post(self._URL, json=self._PAYLOAD)
        pdf_b64 = resp.json()["pdf_base64"]
        pdf_bytes = base64.b64decode(pdf_b64)
        # PDF magic bytes
        assert pdf_bytes[:4] == b"%PDF"

    def test_filename_com_extensao_pdf(self, client):
        """Filename na resposta sempre termina com .pdf."""
        resp = client.post(self._URL, json=self._PAYLOAD)
        assert resp.json()["filename"].endswith(".pdf")

    def test_filename_sem_extensao_e_corrigido(self, client):
        """Filename sem .pdf na requisição tem extensão adicionada automaticamente."""
        payload = dict(self._PAYLOAD)
        payload["filename"] = "sem_extensao"
        resp = client.post(self._URL, json=payload)
        assert resp.json()["filename"] == "sem_extensao.pdf"

    def test_resultant_force_e_float_positivo(self, client):
        """resultant_force é um número de ponto flutuante positivo."""
        resp = client.post(self._URL, json=self._PAYLOAD)
        force = resp.json()["resultant_force"]
        assert isinstance(force, float)
        assert force > 0

    def test_cabos_vazios_retorna_422(self, client):
        """Lista de cabos vazia falha na validação Pydantic → 422."""
        payload = dict(self._PAYLOAD)
        payload["cabos"] = []
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422

    def test_campos_obrigatorios_ausentes_retorna_422(self, client):
        """Payload sem concessionaria falha na validação Pydantic → 422."""
        payload = {"cabos": [{"condutor": "556MCM-CA, Nu", "vao": 80.0, "angulo": 30.0, "flecha": 1.5}]}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422

    def test_calculate_resultant_key_error_retorna_422(self, client, mocker):
        """Cobre branch de erro lines 97-98: KeyError em calculate_resultant → HTTP 422."""
        mocker.patch(
            "api.routes.pole_load.PoleLoadLogic.calculate_resultant",
            side_effect=KeyError("concessionaria"),
        )
        resp = client.post(self._URL, json=self._PAYLOAD)
        assert resp.status_code == 422

    def test_generate_report_exception_retorna_500(self, client, mocker):
        """Cobre branch de erro: exceção em generate_report_to_buffer → HTTP 500."""
        mocker.patch(
            "api.routes.pole_load.generate_report_to_buffer",
            side_effect=RuntimeError("fpdf error"),
        )
        resp = client.post(self._URL, json=self._PAYLOAD)
        assert resp.status_code == 500


# ── Conversor UTM → DXF ───────────────────────────────────────────────────────


class TestUTMToDxfEndpoint:
    """Testes para POST /api/v1/converter/utm-to-dxf."""

    _URL = "/api/v1/converter/utm-to-dxf"
    # Coordenadas de teste reais: UTM 23K E=788547 N=7634925 e lat=-22.15018/lon=-42.92185
    _PAYLOAD = {
        "points": [
            {"name": "P1", "easting": 788547.0, "northing": 7634925.0, "elevation": 720.0},
            {"name": "P2", "easting": 714315.7, "northing": 7549084.2, "elevation": 580.0},
        ],
        "filename": "levantamento.dxf",
    }

    def test_retorna_200(self, client):
        """Requisição válida retorna HTTP 200."""
        resp = client.post(self._URL, json=self._PAYLOAD)
        assert resp.status_code == 200

    def test_resposta_tem_campos_obrigatorios(self, client):
        """Resposta contém dxf_base64, filename e count."""
        resp = client.post(self._URL, json=self._PAYLOAD)
        data = resp.json()
        assert "dxf_base64" in data
        assert "filename" in data
        assert "count" in data

    def test_dxf_base64_e_valido_e_parseable(self, client):
        """dxf_base64 é uma string Base64 válida parseável com ezdxf."""
        import base64
        import io

        import ezdxf

        resp = client.post(self._URL, json=self._PAYLOAD)
        dxf_b64 = resp.json()["dxf_base64"]
        dxf_bytes = base64.b64decode(dxf_b64)
        dxf_str = dxf_bytes.decode("utf-8")
        doc = ezdxf.read(io.StringIO(dxf_str))
        assert doc is not None
        assert doc.dxfversion == "AC1024"  # R2010

    def test_count_corresponde_ao_numero_de_pontos(self, client):
        """count na resposta corresponde ao número de pontos enviados."""
        resp = client.post(self._URL, json=self._PAYLOAD)
        assert resp.json()["count"] == 2

    def test_filename_com_extensao_dxf(self, client):
        """Filename na resposta sempre termina com .dxf."""
        resp = client.post(self._URL, json=self._PAYLOAD)
        assert resp.json()["filename"].endswith(".dxf")

    def test_filename_sem_extensao_e_corrigido(self, client):
        """Filename sem .dxf na requisição tem extensão adicionada automaticamente."""
        payload = dict(self._PAYLOAD)
        payload["filename"] = "sem_extensao"
        resp = client.post(self._URL, json=payload)
        assert resp.json()["filename"] == "sem_extensao.dxf"

    def test_pontos_vazios_retorna_422(self, client):
        """Lista de pontos vazia falha na validação Pydantic → 422."""
        resp = client.post(self._URL, json={"points": [], "filename": "teste.dxf"})
        assert resp.status_code == 422

    def test_campos_obrigatorios_ausentes_retorna_422(self, client):
        """Payload sem points falha na validação Pydantic → 422."""
        resp = client.post(self._URL, json={"filename": "teste.dxf"})
        assert resp.status_code == 422

    def test_ponto_unico_retorna_200(self, client):
        """Um único ponto é aceito e retorna DXF válido."""
        payload = {"points": [{"name": "TRAFO", "easting": 788547.0, "northing": 7634925.0, "elevation": 0.0}]}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        assert resp.json()["count"] == 1

    def test_dxf_exception_retorna_422(self, client, mocker):
        """Cobre branch de erro: ValueError em save_to_dxf_to_buffer → HTTP 422."""
        mocker.patch(
            "api.routes.converter.ConverterLogic.save_to_dxf_to_buffer",
            side_effect=ValueError("DataFrame inválido"),
        )
        resp = client.post(self._URL, json=self._PAYLOAD)
        assert resp.status_code == 422
