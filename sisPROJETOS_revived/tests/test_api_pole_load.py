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


# ── Esforços em Postes em Lote ────────────────────────────────────────────────


class TestPoleLoadBatchEndpoint:
    """Testes para POST /api/v1/pole-load/batch."""

    _URL = "/api/v1/pole-load/batch"
    _ITEM_LIGHT = {
        "label": "Poste P1",
        "concessionaria": "Light",
        "condicao": "Normal",
        "cabos": [{"condutor": "556MCM-CA, Nu", "vao": 80.0, "angulo": 30.0, "flecha": 1.5}],
    }
    _ITEM_ENEL = {
        "label": "Poste P2",
        "concessionaria": "Enel",
        "condicao": "Normal",
        "cabos": [
            {"condutor": "397MCM-CA, Nu", "vao": 60.0, "angulo": 0.0, "flecha": 1.2},
            {"condutor": "397MCM-CA, Nu", "vao": 60.0, "angulo": 90.0, "flecha": 1.2},
        ],
    }

    def test_single_item_retorna_200(self, client):
        """Um único poste retorna HTTP 200."""
        resp = client.post(self._URL, json={"items": [self._ITEM_LIGHT]})
        assert resp.status_code == 200

    def test_dois_itens_retorna_200(self, client):
        """Dois postes no lote retornam HTTP 200."""
        resp = client.post(self._URL, json={"items": [self._ITEM_LIGHT, self._ITEM_ENEL]})
        assert resp.status_code == 200

    def test_resposta_tem_campos_obrigatorios(self, client):
        """Resposta contém count, success_count, error_count e items."""
        resp = client.post(self._URL, json={"items": [self._ITEM_LIGHT]})
        data = resp.json()
        assert "count" in data
        assert "success_count" in data
        assert "error_count" in data
        assert "items" in data

    def test_count_corresponde_ao_numero_de_postes(self, client):
        """count na resposta corresponde ao número de postes enviados."""
        resp = client.post(self._URL, json={"items": [self._ITEM_LIGHT, self._ITEM_ENEL]})
        assert resp.json()["count"] == 2

    def test_label_preservado_na_resposta(self, client):
        """label fornecido na entrada é preservado no item de resposta."""
        resp = client.post(self._URL, json={"items": [self._ITEM_LIGHT]})
        item = resp.json()["items"][0]
        assert item["label"] == "Poste P1"

    def test_resultant_force_e_float_positivo(self, client):
        """resultant_force no item de sucesso é um float positivo."""
        resp = client.post(self._URL, json={"items": [self._ITEM_LIGHT]})
        item = resp.json()["items"][0]
        assert item["success"] is True
        assert isinstance(item["resultant_force"], float)
        assert item["resultant_force"] > 0

    def test_suggested_poles_presentes_em_sucesso(self, client):
        """suggested_poles presentes no item de sucesso (lista, mesmo que vazia)."""
        resp = client.post(self._URL, json={"items": [self._ITEM_LIGHT]})
        item = resp.json()["items"][0]
        assert "suggested_poles" in item
        assert isinstance(item["suggested_poles"], list)

    def test_concessionaria_invalida_retorna_success_false_sem_abortar(self, client):
        """Concessionária inválida gera success=False mas não aborta os demais itens."""
        bad_item = dict(self._ITEM_LIGHT)
        bad_item["concessionaria"] = "INVALIDA_XYZ"
        resp = client.post(self._URL, json={"items": [bad_item, self._ITEM_ENEL]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["items"][0]["success"] is False
        assert "error" in data["items"][0]
        assert data["items"][1]["success"] is True

    def test_itens_vazios_retorna_422(self, client):
        """Lista de postes vazia falha na validação Pydantic → 422."""
        resp = client.post(self._URL, json={"items": []})
        assert resp.status_code == 422

    def test_exception_nao_aborta_lote(self, client, mocker):
        """Exceção inesperada em um item retorna success=False sem abortar os demais."""
        call_count = [0]

        def side_effect_once(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Falha simulada")
            from modules.pole_load.logic import PoleLoadLogic as _PLL

            return _PLL().calculate_resultant(*args, **kwargs)

        mocker.patch(
            "api.routes.pole_load.PoleLoadLogic.calculate_resultant",
            side_effect=side_effect_once,
        )
        resp = client.post(self._URL, json={"items": [self._ITEM_LIGHT, self._ITEM_ENEL]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["success"] is False
        assert "Falha simulada" in data["items"][0]["error"]
