"""
Testes da API de catenária — sisPROJETOS.

Cobre os endpoints específicos de catenária:
- POST /api/v1/catenary/calculate  (include_curve, NBR 5422 clearance)
- POST /api/v1/catenary/dxf        (geração de DXF Base64 via API — BIM)
- POST /api/v1/catenary/calculate  (verificação de folga ao solo NBR 5422 min_clearance_m)
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


# ── Catenária: verificação de folga ao solo (NBR 5422) ────────────────────────


class TestCatenaryNBR5422Clearance:
    """Testa o campo opcional min_clearance_m para verificação de folga ao solo (NBR 5422)."""

    _URL = "/api/v1/catenary/calculate"

    def _payload(self, **extra):
        base = {
            "span": 80.0,
            "ha": 9.0,
            "hb": 9.0,
            "tension_daN": 500.0,
            "weight_kg_m": 0.779,
        }
        base.update(extra)
        return base

    def test_without_clearance_within_clearance_is_none(self, client):
        """Sem min_clearance_m → within_clearance ausente da resposta (ou None)."""
        resp = client.post(self._URL, json=self._payload())
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("within_clearance") is None

    def test_clearance_ok_when_sag_below_limit(self, client):
        """Flecha < min_clearance_m → within_clearance=True; verifica margem positiva."""
        # 80 m span, 500 daN, 0.779 kg/m → sag ≈ 1.22 m (well below 6.0 m)
        resp = client.post(self._URL, json=self._payload(min_clearance_m=6.0))
        assert resp.status_code == 200
        data = resp.json()
        assert data["within_clearance"] is True
        assert data["sag"] < 6.0
        assert 6.0 - data["sag"] > 0  # positive clearance margin

    def test_clearance_fail_when_sag_above_limit(self, client):
        """Flecha > min_clearance_m → within_clearance=False."""
        # Tiny clearance (0.5 m) → sag (≈1.22 m) exceeds limit
        resp = client.post(self._URL, json=self._payload(min_clearance_m=0.5))
        assert resp.status_code == 200
        data = resp.json()
        assert data["within_clearance"] is False
        assert data["sag"] > 0.5

    def test_clearance_boundary_exact(self, client):
        """Flecha == min_clearance_m → within_clearance=True (sag ≤ limit)."""
        # Get the actual sag first, then use it as the limit
        resp_base = client.post(self._URL, json=self._payload())
        sag = resp_base.json()["sag"]
        resp = client.post(self._URL, json=self._payload(min_clearance_m=sag))
        assert resp.status_code == 200
        assert resp.json()["within_clearance"] is True

    def test_clearance_returns_sag_unchanged(self, client):
        """min_clearance_m não altera o valor de sag calculado."""
        resp_base = client.post(self._URL, json=self._payload())
        resp_limit = client.post(self._URL, json=self._payload(min_clearance_m=6.0))
        assert resp_base.json()["sag"] == pytest.approx(resp_limit.json()["sag"], rel=1e-9)


# ── Tabela de Folgas NBR 5422 / PRODIST Módulo 6 ─────────────────────────────


class TestCatenaryNBR5422ClearancesTable:
    """Testes para GET /api/v1/catenary/clearances (tabela de folgas mínimas)."""

    _URL = "/api/v1/catenary/clearances"

    def test_clearances_retorna_200(self, client):
        """GET /clearances retorna HTTP 200."""
        resp = client.get(self._URL)
        assert resp.status_code == 200

    def test_clearances_tem_campos_obrigatorios(self, client):
        """Resposta contém clearances, count e note."""
        data = client.get(self._URL).json()
        assert "clearances" in data
        assert "count" in data
        assert "note" in data

    def test_clearances_count_igual_len_lista(self, client):
        """Campo count reflete o tamanho real da lista."""
        data = client.get(self._URL).json()
        assert data["count"] == len(data["clearances"])

    def test_clearances_bt_urbana_tem_6m(self, client):
        """BT_URBANA deve ter folga mínima de 6.0 m (NBR 5422 / PRODIST Módulo 6)."""
        data = client.get(self._URL).json()
        bt_urbana = next((c for c in data["clearances"] if c["network_type"] == "BT_URBANA"), None)
        assert bt_urbana is not None
        assert bt_urbana["min_clearance_m"] == pytest.approx(6.0)

    def test_clearances_bt_rural_tem_5_5m(self, client):
        """BT_RURAL deve ter folga mínima de 5.5 m."""
        data = client.get(self._URL).json()
        bt_rural = next((c for c in data["clearances"] if c["network_type"] == "BT_RURAL"), None)
        assert bt_rural is not None
        assert bt_rural["min_clearance_m"] == pytest.approx(5.5)

    def test_clearances_mt_maior_que_bt(self, client):
        """Folga MT deve ser maior que folga BT (hierarquia de segurança)."""
        data = client.get(self._URL).json()
        clearances = {c["network_type"]: c["min_clearance_m"] for c in data["clearances"]}
        assert clearances["MT_URBANA"] > clearances["BT_URBANA"]
        assert clearances["MT_RURAL"] > clearances["BT_RURAL"]


# ── TestCatenaryBatchEndpoint ────────────────────────────────────────────────


class TestCatenaryBatchEndpoint:
    """Testes para POST /api/v1/catenary/batch — cálculo em lote (BIM multi-vão)."""

    _URL = "/api/v1/catenary/batch"
    _ITEM_100M = {"span": 100.0, "tension_daN": 2000.0, "ha": 10.0, "hb": 10.0, "weight_kg_m": 1.6}
    _ITEM_500M = {"span": 500.0, "tension_daN": 2000.0, "ha": 10.0, "hb": 12.0, "weight_kg_m": 1.6}
    _ITEM_1KM = {"span": 1000.0, "tension_daN": 2000.0, "ha": 12.0, "hb": 12.0, "weight_kg_m": 1.6}

    def test_batch_single_item_success(self, client):
        """Lote com um item válido retorna HTTP 200 com success=True."""
        resp = client.post(self._URL, json={"items": [self._ITEM_100M]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["success_count"] == 1
        assert data["error_count"] == 0
        assert data["items"][0]["success"] is True

    def test_batch_three_spans_returns_three_items(self, client):
        """Lote com 3 vãos retorna 3 itens."""
        resp = client.post(
            self._URL,
            json={"items": [self._ITEM_100M, self._ITEM_500M, self._ITEM_1KM]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3
        assert data["success_count"] == 3
        assert data["error_count"] == 0

    def test_batch_sag_increases_with_span(self, client):
        """Flecha deve aumentar com o vão (para mesma tensão e peso) — propriedade física."""
        resp = client.post(
            self._URL,
            json={"items": [self._ITEM_100M, self._ITEM_500M, self._ITEM_1KM]},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        sag_100 = items[0]["sag"]
        sag_500 = items[1]["sag"]
        sag_1000 = items[2]["sag"]
        assert sag_100 < sag_500 < sag_1000

    def test_batch_label_preserved_in_response(self, client):
        """Label fornecido na entrada deve ser retornado na saída."""
        item = {**self._ITEM_100M, "label": "Vão P1-P2"}
        resp = client.post(self._URL, json={"items": [item]})
        assert resp.status_code == 200
        assert resp.json()["items"][0]["label"] == "Vão P1-P2"

    def test_batch_index_matches_input_order(self, client):
        """Campo 'index' deve corresponder à posição na lista de entrada."""
        resp = client.post(
            self._URL,
            json={"items": [self._ITEM_100M, self._ITEM_500M]},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert items[0]["index"] == 0
        assert items[1]["index"] == 1

    def test_batch_with_clearance_check(self, client):
        """Vão com min_clearance_m deve retornar within_clearance na resposta."""
        item = {**self._ITEM_100M, "min_clearance_m": 6.0}
        resp = client.post(self._URL, json={"items": [item]})
        assert resp.status_code == 200
        result = resp.json()["items"][0]
        assert result["within_clearance"] is not None
        assert isinstance(result["within_clearance"], bool)

    def test_batch_without_clearance_returns_none(self, client):
        """Vão sem min_clearance_m deve retornar within_clearance=None."""
        resp = client.post(self._URL, json={"items": [self._ITEM_100M]})
        assert resp.status_code == 200
        assert resp.json()["items"][0]["within_clearance"] is None

    def test_batch_invalid_item_does_not_abort_others(self, client):
        """Item com weight_kg_m=0 falha mas os demais são calculados."""
        invalid_item = {**self._ITEM_100M, "weight_kg_m": 0.0}
        resp = client.post(
            self._URL,
            json={"items": [self._ITEM_100M, invalid_item, self._ITEM_500M]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3
        assert data["success_count"] == 2
        assert data["error_count"] == 1
        assert data["items"][1]["success"] is False
        assert data["items"][1]["error"] is not None
        assert data["items"][0]["success"] is True
        assert data["items"][2]["success"] is True

    def test_batch_empty_list_returns_422(self, client):
        """Lista vazia deve retornar HTTP 422 (violação de min_length=1)."""
        resp = client.post(self._URL, json={"items": []})
        assert resp.status_code == 422

    def test_batch_response_fields_present(self, client):
        """Resposta deve conter todos os campos esperados do schema."""
        resp = client.post(self._URL, json={"items": [self._ITEM_100M]})
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "success_count" in data
        assert "error_count" in data
        assert "items" in data
        item = data["items"][0]
        assert "index" in item
        assert "success" in item
        assert "sag" in item
        assert "tension" in item
        assert "catenary_constant" in item
