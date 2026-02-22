"""
Testes unitários e de integração para endpoints de Esforços em Postes e
Conversor UTM→DXF da API REST do sisPROJETOS.

Cobre:
- POST /api/v1/pole-load/report  (relatório PDF em Base64, fpdf2)
- POST /api/v1/converter/utm-to-dxf (pipeline BIM KML→UTM→DXF via API)

Extraído de ``tests/test_api_bim.py`` para manter arquivos abaixo de 500 linhas
(regra de modularização do projeto).
"""

import base64

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Cliente de testes FastAPI (reutilizado em todos os testes do módulo)."""
    from src.api.app import create_app

    app = create_app()
    return TestClient(app)


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
        resp = client.post(self._URL, json=self._PAYLOAD)
        pdf_b64 = resp.json()["pdf_base64"]
        pdf_bytes = base64.b64decode(pdf_b64)
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
        """Cobre branch de erro: KeyError em calculate_resultant → HTTP 422."""
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
