"""
Testes para padrões normativos (ABNT / ANEEL / PRODIST / Concessionárias) na API REST.

Cobre os endpoints:
- GET  /api/v1/electrical/standards
- POST /api/v1/electrical/voltage-drop  (campo standard_name)
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Cliente de testes FastAPI (reutilizado em todos os testes do módulo)."""
    from src.api.app import create_app

    app = create_app()
    return TestClient(app)


# ── Padrões Normativos (ABNT / ANEEL / PRODIST / Concessionárias) ─────────────


class TestElectricalStandardsEndpoint:
    """Testa o endpoint GET /api/v1/electrical/standards."""

    _URL = "/api/v1/electrical/standards"

    def test_returns_200(self, client):
        resp = client.get(self._URL)
        assert resp.status_code == 200

    def test_returns_list(self, client):
        data = client.get(self._URL).json()
        assert isinstance(data, list)

    def test_returns_five_standards(self, client):
        data = client.get(self._URL).json()
        assert len(data) == 5

    def test_nbr_5410_present(self, client):
        names = [s["name"] for s in client.get(self._URL).json()]
        assert "NBR 5410" in names

    def test_prodist_bt_present(self, client):
        names = [s["name"] for s in client.get(self._URL).json()]
        assert "PRODIST Módulo 8 — BT" in names

    def test_light_concessionaire_present(self, client):
        names = [s["name"] for s in client.get(self._URL).json()]
        assert "Light — BT (PRODIST Módulo 8)" in names

    def test_each_standard_has_required_fields(self, client):
        for s in client.get(self._URL).json():
            assert "name" in s
            assert "source" in s
            assert "max_drop_percent" in s
            assert "overrides_abnt" in s
            assert "override_toast_pt_br" in s

    def test_nbr_5410_does_not_override_abnt(self, client):
        nbr = next(s for s in client.get(self._URL).json() if s["name"] == "NBR 5410")
        assert nbr["overrides_abnt"] is False
        assert nbr["override_toast_pt_br"] is None

    def test_prodist_overrides_abnt_with_toast(self, client):
        prodist = next(s for s in client.get(self._URL).json() if s["name"] == "PRODIST Módulo 8 — BT")
        assert prodist["overrides_abnt"] is True
        assert "PRODIST" in prodist["override_toast_pt_br"]

    def test_concessionaire_toast_in_portuguese(self, client):
        light = next(s for s in client.get(self._URL).json() if "Light" in s["name"])
        assert "⚠️" in light["override_toast_pt_br"]
        assert "Light" in light["override_toast_pt_br"]


class TestElectricalVoltageDropWithStandard:
    """Testa a integração de padrões normativos no endpoint POST /voltage-drop."""

    _URL = "/api/v1/electrical/voltage-drop"

    def _valid_payload(self, **overrides):
        base = {
            "power_kw": 50.0,
            "distance_m": 200.0,
            "voltage_v": 220.0,
            "material": "Alumínio",
            "section_mm2": 35.0,
            "cos_phi": 0.92,
            "phases": 3,
        }
        base.update(overrides)
        return base

    def test_default_standard_is_nbr5410(self, client):
        """Sem standard_name → padrão NBR 5410."""
        resp = client.post(self._URL, json=self._valid_payload())
        assert resp.status_code == 200
        data = resp.json()
        assert data["standard_name"] == "NBR 5410"
        assert data["override_toast"] is None

    def test_response_contains_standard_name(self, client):
        resp = client.post(self._URL, json=self._valid_payload())
        assert "standard_name" in resp.json()

    def test_response_contains_override_toast(self, client):
        resp = client.post(self._URL, json=self._valid_payload())
        assert "override_toast" in resp.json()

    def test_explicit_nbr5410_standard(self, client):
        payload = self._valid_payload(standard_name="NBR 5410")
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        assert resp.json()["standard_name"] == "NBR 5410"

    def test_prodist_bt_widens_limit(self, client):
        """Com PRODIST BT (8%), queda que excederia NBR 5410 (5%) fica permitida."""
        # section=50mm², dist=100m → drop≈5.826% (> 5%, < 8%)
        payload = self._valid_payload(section_mm2=50.0, distance_m=100.0, standard_name="PRODIST Módulo 8 — BT")
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["standard_name"] == "PRODIST Módulo 8 — BT"
        # NBR 5410 would reject it; PRODIST limit is 8%
        assert data["percentage_drop"] > 5.0
        assert data["allowed"] is True

    def test_prodist_bt_has_override_toast(self, client):
        payload = self._valid_payload(standard_name="PRODIST Módulo 8 — BT")
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["override_toast"] is not None
        assert "PRODIST" in data["override_toast"]
        assert "⚠️" in data["override_toast"]

    def test_light_concessionaire_standard(self, client):
        payload = self._valid_payload(standard_name="Light — BT (PRODIST Módulo 8)")
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["standard_name"] == "Light — BT (PRODIST Módulo 8)"
        assert data["override_toast"] is not None
        assert "Light" in data["override_toast"]

    def test_enel_concessionaire_standard(self, client):
        payload = self._valid_payload(standard_name="Enel — BT (PRODIST Módulo 8)")
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "Enel" in data["standard_name"]
        assert data["override_toast"] is not None

    def test_prodist_mt_standard(self, client):
        payload = self._valid_payload(standard_name="PRODIST Módulo 8 — MT")
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        assert resp.json()["standard_name"] == "PRODIST Módulo 8 — MT"

    def test_unknown_standard_returns_422(self, client):
        payload = self._valid_payload(standard_name="NORMA_INEXISTENTE")
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "NORMA_INEXISTENTE" in detail
        assert "standards" in detail  # References the standards list endpoint

    def test_allowed_false_when_exceeds_even_prodist(self, client):
        """Queda acima de 8% é rejeitada mesmo com PRODIST BT."""
        # section=35mm², dist=100m → drop≈8.323% (> 8%)
        payload = self._valid_payload(
            section_mm2=35.0, distance_m=100.0, power_kw=50.0, standard_name="PRODIST Módulo 8 — BT"
        )
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["percentage_drop"] > 8.0
        assert data["allowed"] is False

    def test_nbr5410_rejects_what_prodist_allows(self, client):
        """Mesma queda: NBR 5410 rejeita, PRODIST BT aceita."""
        # section=50mm², dist=100m → drop≈5.826%
        payload_nbr = self._valid_payload(section_mm2=50.0, distance_m=100.0)
        payload_prodist = self._valid_payload(
            section_mm2=50.0, distance_m=100.0, standard_name="PRODIST Módulo 8 — BT"
        )
        resp_nbr = client.post(self._URL, json=payload_nbr)
        resp_prodist = client.post(self._URL, json=payload_prodist)
        assert resp_nbr.status_code == 200
        assert resp_prodist.status_code == 200
        # Same physics, different normative conclusion
        assert resp_nbr.json()["percentage_drop"] == pytest.approx(resp_prodist.json()["percentage_drop"], rel=1e-6)
        assert resp_nbr.json()["allowed"] is False
        assert resp_prodist.json()["allowed"] is True


class TestVoltageBatchEndpoint:
    """POST /api/v1/electrical/batch — Cálculo em lote de queda de tensão."""

    _URL = "/api/v1/electrical/batch"

    @pytest.fixture
    def client(self):
        from api.app import create_app

        return TestClient(create_app())

    _ITEM_220V = {
        "power_kw": 30.0,
        "distance_m": 150.0,
        "voltage_v": 220.0,
        "material": "Alumínio",
        "section_mm2": 50.0,
        "cos_phi": 0.92,
        "phases": 3,
    }

    _ITEM_127V = {
        "power_kw": 10.0,
        "distance_m": 100.0,
        "voltage_v": 127.0,
        "material": "Cobre",
        "section_mm2": 16.0,
        "cos_phi": 0.85,
        "phases": 1,
    }

    def test_batch_single_circuit_success(self, client):
        """Lote com um circuito deve retornar HTTP 200 e success=True."""
        resp = client.post(self._URL, json={"items": [self._ITEM_220V]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["success_count"] == 1
        assert data["error_count"] == 0
        assert data["items"][0]["success"] is True

    def test_batch_two_circuits_returns_two_items(self, client):
        """Lote com dois circuitos deve retornar dois itens."""
        resp = client.post(self._URL, json={"items": [self._ITEM_220V, self._ITEM_127V]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["success_count"] == 2
        assert data["items"][0]["index"] == 0
        assert data["items"][1]["index"] == 1

    def test_batch_label_preserved(self, client):
        """Rótulo opcional deve ser preservado na resposta."""
        item = {**self._ITEM_220V, "label": "Ramal Residencial"}
        resp = client.post(self._URL, json={"items": [item]})
        assert resp.status_code == 200
        assert resp.json()["items"][0]["label"] == "Ramal Residencial"

    def test_batch_default_standard_is_nbr5410(self, client):
        """Padrão padrão deve ser NBR 5410 quando standard_name não informado."""
        resp = client.post(self._URL, json={"items": [self._ITEM_220V]})
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["standard_name"] == "NBR 5410"
        assert item["override_toast"] is None

    def test_batch_prodist_standard_applied(self, client):
        """Quando PRODIST BT selecionado, override_toast deve estar presente."""
        item = {**self._ITEM_220V, "standard_name": "PRODIST Módulo 8 — BT"}
        resp = client.post(self._URL, json={"items": [item]})
        assert resp.status_code == 200
        result = resp.json()["items"][0]
        assert result["success"] is True
        assert result["standard_name"] == "PRODIST Módulo 8 — BT"
        assert result["override_toast"] is not None
        assert "PRODIST" in result["override_toast"]

    def test_batch_unknown_standard_returns_failure_not_abort(self, client):
        """Standard desconhecido no item deve retornar failure sem abortar os demais."""
        bad_item = {**self._ITEM_220V, "standard_name": "NORMA_INEXISTENTE"}
        resp = client.post(self._URL, json={"items": [bad_item, self._ITEM_127V]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["success_count"] == 1
        assert data["error_count"] == 1
        assert data["items"][0]["success"] is False
        assert "NORMA_INEXISTENTE" in data["items"][0]["error"]
        assert data["items"][1]["success"] is True

    def test_batch_none_result_does_not_abort_others_via_mock(self, client, mocker):
        """None result no item deve retornar failure sem abortar os demais circuitos."""
        # First call returns real result, subsequent calls return None
        import itertools

        real_results = [
            {
                "current": 10.0,
                "delta_v_volts": 2.0,
                "percentage_drop": 0.91,
                "allowed": True,
            },
            None,
        ]
        mocker.patch(
            "src.api.routes.electrical.ElectricalLogic.calculate_voltage_drop",
            side_effect=itertools.chain(real_results),
        )
        resp = client.post(self._URL, json={"items": [self._ITEM_220V, self._ITEM_127V]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["success"] is True
        assert data["items"][1]["success"] is False
        assert "inválidos" in data["items"][1]["error"]

    def test_batch_response_fields_present(self, client):
        """Todos os campos esperados devem estar presentes na resposta."""
        resp = client.post(self._URL, json={"items": [self._ITEM_220V]})
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "success_count" in data
        assert "error_count" in data
        assert "items" in data
        item = data["items"][0]
        assert "current" in item
        assert "delta_v_volts" in item
        assert "percentage_drop" in item
        assert "allowed" in item

    def test_batch_empty_list_returns_422(self, client):
        """Lista vazia deve retornar HTTP 422 (violação de min_length=1)."""
        resp = client.post(self._URL, json={"items": []})
        assert resp.status_code == 422

    def test_batch_exception_path_via_mock(self, client, mocker):
        """Erro inesperado no cálculo deve produzir success=False sem abortar lote."""
        mocker.patch(
            "src.api.routes.electrical.ElectricalLogic.calculate_voltage_drop",
            side_effect=RuntimeError("falha simulada"),
        )
        resp = client.post(self._URL, json={"items": [self._ITEM_220V, self._ITEM_127V]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 0
        assert data["error_count"] == 2
        for item in data["items"]:
            assert item["success"] is False
            assert "falha simulada" in item["error"]

    def test_batch_none_result_via_mock(self, client, mocker):
        """Quando calculate_voltage_drop retorna None, item deve ter success=False — cobre linhas 175-183."""
        mocker.patch(
            "src.api.routes.electrical.ElectricalLogic.calculate_voltage_drop",
            return_value=None,
        )
        resp = client.post(self._URL, json={"items": [self._ITEM_220V]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 0
        assert data["error_count"] == 1
        assert data["items"][0]["success"] is False
        assert "inválidos" in data["items"][0]["error"]
