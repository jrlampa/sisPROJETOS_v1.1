"""
Testes da API de catenária — sisPROJETOS.

Cobre os endpoints específicos de catenária:
- POST /api/v1/catenary/calculate  (include_curve, NBR 5422 clearance)
- POST /api/v1/catenary/dxf        (geração de DXF Base64 via API — BIM)
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


_CALC_URL = "/api/v1/catenary/calculate"
_DXF_URL = "/api/v1/catenary/dxf"

_BASE_PAYLOAD = {
    "span": 80.0,
    "ha": 9.0,
    "hb": 9.0,
    "tension_daN": 500.0,
    "weight_kg_m": 0.779,
}


# ── include_curve ──────────────────────────────────────────────────────────────


class TestCatenaryIncludeCurve:
    """Testa o campo include_curve no endpoint /calculate."""

    def test_sem_include_curve_retorna_none(self, client):
        """Por padrão (include_curve=false), curve_x e curve_y devem ser null."""
        resp = client.post(_CALC_URL, json=_BASE_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["curve_x"] is None
        assert data["curve_y"] is None

    def test_include_curve_false_explicito(self, client):
        """include_curve=false explícito → curve_x/curve_y null."""
        payload = {**_BASE_PAYLOAD, "include_curve": False}
        resp = client.post(_CALC_URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["curve_x"] is None
        assert data["curve_y"] is None

    def test_include_curve_true_retorna_listas(self, client):
        """include_curve=true → curve_x e curve_y devem ser listas não vazias."""
        payload = {**_BASE_PAYLOAD, "include_curve": True}
        resp = client.post(_CALC_URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["curve_x"], list)
        assert isinstance(data["curve_y"], list)
        assert len(data["curve_x"]) > 0
        assert len(data["curve_y"]) > 0

    def test_curve_points_100_valores(self, client):
        """A curva deve ter exatamente 100 pontos (conforme CatenaryLogic)."""
        payload = {**_BASE_PAYLOAD, "include_curve": True}
        resp = client.post(_CALC_URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["curve_x"]) == 100
        assert len(data["curve_y"]) == 100

    def test_curve_x_inicia_em_zero(self, client):
        """O primeiro ponto X da curva deve ser 0.0 (início do vão)."""
        payload = {**_BASE_PAYLOAD, "include_curve": True}
        resp = client.post(_CALC_URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert abs(data["curve_x"][0]) < 1e-9

    def test_curve_x_termina_no_vao(self, client):
        """O último ponto X deve ser igual ao vão (80.0 m)."""
        payload = {**_BASE_PAYLOAD, "include_curve": True}
        resp = client.post(_CALC_URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert abs(data["curve_x"][-1] - _BASE_PAYLOAD["span"]) < 1e-6

    def test_curve_inclui_campos_de_calculo(self, client):
        """A resposta com curva ainda deve incluir sag, tension e catenary_constant."""
        payload = {**_BASE_PAYLOAD, "include_curve": True}
        resp = client.post(_CALC_URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sag"] > 0
        assert data["tension"] == _BASE_PAYLOAD["tension_daN"]
        assert data["catenary_constant"] > 0


# ── POST /catenary/dxf ─────────────────────────────────────────────────────────


class TestCatenaryDxfEndpoint:
    """Testa o endpoint POST /api/v1/catenary/dxf."""

    def test_retorna_200_com_dxf_base64(self, client):
        """Requisição válida deve retornar 200 e um dxf_base64 não vazio."""
        resp = client.post(_DXF_URL, json=_BASE_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert "dxf_base64" in data
        assert len(data["dxf_base64"]) > 0

    def test_dxf_base64_decodificavel(self, client):
        """O campo dxf_base64 deve ser um Base64 válido (RFC 4648)."""
        resp = client.post(_DXF_URL, json=_BASE_PAYLOAD)
        assert resp.status_code == 200
        dxf_bytes = base64.b64decode(resp.json()["dxf_base64"])
        assert len(dxf_bytes) > 0

    def test_dxf_conteudo_valido_ezdxf(self, client):
        """O DXF decodificado deve ser um arquivo DXF válido legível pelo ezdxf."""
        import io

        import ezdxf

        resp = client.post(_DXF_URL, json=_BASE_PAYLOAD)
        assert resp.status_code == 200
        dxf_bytes = base64.b64decode(resp.json()["dxf_base64"])
        doc = ezdxf.read(io.StringIO(dxf_bytes.decode("utf-8", errors="replace")))
        assert doc is not None

    def test_dxf_tem_layer_catenary_curve(self, client):
        """O DXF gerado deve conter o layer CATENARY_CURVE."""
        import io

        import ezdxf

        resp = client.post(_DXF_URL, json=_BASE_PAYLOAD)
        dxf_bytes = base64.b64decode(resp.json()["dxf_base64"])
        doc = ezdxf.read(io.StringIO(dxf_bytes.decode("utf-8", errors="replace")))
        layer_names = [layer.dxf.name for layer in doc.layers]
        assert "CATENARY_CURVE" in layer_names

    def test_retorna_sag_e_constante(self, client):
        """A resposta deve incluir sag e catenary_constant para referência."""
        resp = client.post(_DXF_URL, json=_BASE_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sag"] > 0
        assert data["catenary_constant"] > 0

    def test_filename_padrao(self, client):
        """Sem filename, deve usar 'catenaria.dxf'."""
        resp = client.post(_DXF_URL, json=_BASE_PAYLOAD)
        assert resp.status_code == 200
        assert resp.json()["filename"] == "catenaria.dxf"

    def test_filename_personalizado(self, client):
        """Com filename personalizado, deve ser refletido na resposta."""
        payload = {**_BASE_PAYLOAD, "filename": "trecho_01"}
        resp = client.post(_DXF_URL, json=payload)
        assert resp.status_code == 200
        # .dxf é adicionado automaticamente se ausente
        assert resp.json()["filename"] == "trecho_01.dxf"

    def test_filename_com_extensao_dxf(self, client):
        """Filename com .dxf já incluído não deve duplicar a extensão."""
        payload = {**_BASE_PAYLOAD, "filename": "meu_projeto.dxf"}
        resp = client.post(_DXF_URL, json=payload)
        assert resp.status_code == 200
        assert resp.json()["filename"] == "meu_projeto.dxf"

    def test_peso_zero_retorna_422(self, client):
        """Peso linear zero deve retornar 422 (inválido para DXF)."""
        payload = {**_BASE_PAYLOAD, "weight_kg_m": 0}
        resp = client.post(_DXF_URL, json=payload)
        assert resp.status_code == 422

    def test_vao_negativo_retorna_422(self, client):
        """Vão negativo deve retornar 422 antes de qualquer cálculo."""
        payload = {**_BASE_PAYLOAD, "span": -10.0}
        resp = client.post(_DXF_URL, json=payload)
        assert resp.status_code == 422

    def test_resultado_none_retorna_422(self, client, mocker):
        """Quando calculate_catenary retorna None, o endpoint DXF deve retornar 422."""
        mocker.patch(
            "src.api.routes.catenary.CatenaryLogic.calculate_catenary",
            return_value=None,
        )
        resp = client.post(_DXF_URL, json=_BASE_PAYLOAD)
        assert resp.status_code == 422
        assert "inválidos" in resp.json()["detail"].lower()
