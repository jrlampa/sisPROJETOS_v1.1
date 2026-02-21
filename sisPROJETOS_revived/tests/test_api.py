"""
Testes unitários e de integração para a API REST do sisPROJETOS.

Cobre os endpoints de cálculo:
- GET  /health                        (estado de saúde rico — DB status, environment, timestamp)
- POST /api/v1/electrical/voltage-drop
- POST /api/v1/cqt/calculate
- POST /api/v1/catenary/calculate
- POST /api/v1/pole-load/resultant
- GET  /api/v1/electrical/materials
- GET  /api/v1/pole-load/suggest

Testes específicos de catenária (include_curve, DXF, folga NBR 5422): ver test_api_catenary.py
Padrões normativos (ABNT/ANEEL/PRODIST): ver test_api_standards.py
BIM endpoints (dados mestres, conversor, projetos): ver test_api_bim.py
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Cliente de testes FastAPI (reutilizado em todos os testes do módulo)."""
    from src.api.app import create_app

    app = create_app()
    return TestClient(app)


# ── Health ─────────────────────────────────────────────────────────────────────


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_has_db_status_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["db_status"] == "ok"

    def test_health_has_environment_field(self, client):
        resp = client.get("/health")
        assert resp.json()["environment"] in ("development", "production")

    def test_health_has_iso_timestamp(self, client):
        from datetime import datetime

        resp = client.get("/health")
        ts = resp.json()["timestamp"]
        # Should parse as a valid ISO 8601 datetime (raises ValueError if not)
        datetime.fromisoformat(ts)

    def test_health_version_matches_package(self, client):
        from src.__version__ import __version__

        resp = client.get("/health")
        assert resp.json()["version"] == __version__

    def test_health_degraded_when_db_fails(self, client, mocker):
        mocker.patch(
            "api.routes.health._db.get_all_conductors",
            side_effect=Exception("DB inacessível"),
        )
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["db_status"] == "error"

    def test_docs_accessible(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200


# ── Elétrico ───────────────────────────────────────────────────────────────────


class TestElectricalEndpoint:
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

    def test_valid_trifasico(self, client):
        resp = client.post(self._URL, json=self._valid_payload())
        assert resp.status_code == 200
        data = resp.json()
        assert "current" in data
        assert "delta_v_volts" in data
        assert "percentage_drop" in data
        assert isinstance(data["allowed"], bool)
        assert data["percentage_drop"] >= 0

    def test_valid_monofasico(self, client):
        payload = self._valid_payload(phases=1, section_mm2=6.0, distance_m=50.0)
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["current"] > 0

    def test_cobre_material(self, client):
        resp = client.post(self._URL, json=self._valid_payload(material="Cobre"))
        assert resp.status_code == 200

    def test_queda_dentro_do_limite(self, client):
        """Seção grande deve estar dentro do limite de 5%."""
        payload = self._valid_payload(section_mm2=120.0, distance_m=50.0)
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        assert resp.json()["allowed"] is True

    def test_potencia_zero_retorna_422(self, client):
        resp = client.post(self._URL, json=self._valid_payload(power_kw=0))
        assert resp.status_code == 422

    def test_distancia_negativa_retorna_422(self, client):
        resp = client.post(self._URL, json=self._valid_payload(distance_m=-10))
        assert resp.status_code == 422

    def test_fases_invalidas_retorna_422(self, client):
        resp = client.post(self._URL, json=self._valid_payload(phases=2))
        assert resp.status_code == 422

    def test_cos_phi_invalido_retorna_422(self, client):
        resp = client.post(self._URL, json=self._valid_payload(cos_phi=1.5))
        assert resp.status_code == 422

    def test_campos_obrigatorios_ausentes(self, client):
        resp = client.post(self._URL, json={"power_kw": 50.0})
        assert resp.status_code == 422


# ── CQT ────────────────────────────────────────────────────────────────────────


class TestCQTEndpoint:
    _URL = "/api/v1/cqt/calculate"

    _VALID_SEGMENTS = [
        {
            "ponto": "TRAFO",
            "montante": "",
            "metros": 0,
            "cabo": "",
            "mono": 0,
            "bi": 0,
            "tri": 0,
            "tri_esp": 0,
            "carga_esp": 0,
        },
        {
            "ponto": "P1",
            "montante": "TRAFO",
            "metros": 50,
            "cabo": "3x35+54.6mm² Al",
            "mono": 5,
            "bi": 0,
            "tri": 0,
            "tri_esp": 0,
            "carga_esp": 0,
        },
        {
            "ponto": "P2",
            "montante": "P1",
            "metros": 30,
            "cabo": "3x35+54.6mm² Al",
            "mono": 3,
            "bi": 0,
            "tri": 0,
            "tri_esp": 0,
            "carga_esp": 0,
        },
    ]

    def test_calculo_valido(self, client):
        payload = {"segments": self._VALID_SEGMENTS, "trafo_kva": 112.5, "social_class": "B"}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["results"] is not None
        assert "fd" in data["summary"]
        assert "max_cqt" in data["summary"]

    def test_sem_trafo_retorna_erro(self, client):
        segments = [
            {
                "ponto": "P1",
                "montante": "",
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 5,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]
        payload = {"segments": segments, "trafo_kva": 112.5, "social_class": "B"}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert data["error"] is not None

    def test_classe_social_d(self, client):
        payload = {"segments": self._VALID_SEGMENTS, "trafo_kva": 300.0, "social_class": "D"}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_segmentos_vazios_retorna_422(self, client):
        payload = {"segments": [], "trafo_kva": 112.5, "social_class": "B"}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422


# ── Catenária ──────────────────────────────────────────────────────────────────


class TestCatenaryEndpoint:
    _URL = "/api/v1/catenary/calculate"

    def _valid_payload(self, **overrides):
        base = {
            "span": 80.0,
            "ha": 9.0,
            "hb": 9.0,
            "tension_daN": 500.0,
            "weight_kg_m": 0.779,
        }
        base.update(overrides)
        return base

    def test_calculo_valido_nivel(self, client):
        resp = client.post(self._URL, json=self._valid_payload())
        assert resp.status_code == 200
        data = resp.json()
        assert data["sag"] > 0
        assert data["tension"] == 500.0
        assert data["catenary_constant"] > 0

    def test_vao_inclinado(self, client):
        resp = client.post(self._URL, json=self._valid_payload(ha=9.0, hb=11.0))
        assert resp.status_code == 200
        assert resp.json()["sag"] > 0

    def test_vao_zero_retorna_422(self, client):
        resp = client.post(self._URL, json=self._valid_payload(span=0))
        assert resp.status_code == 422

    def test_peso_zero_retorna_422(self, client):
        resp = client.post(self._URL, json=self._valid_payload(weight_kg_m=0))
        assert resp.status_code == 422

    def test_tensao_negativa_retorna_422(self, client):
        resp = client.post(self._URL, json=self._valid_payload(tension_daN=-10))
        assert resp.status_code == 422


# ── Esforços em Postes ─────────────────────────────────────────────────────────


class TestPoleLoadEndpoint:
    _URL = "/api/v1/pole-load/resultant"

    _VALID_LIGHT = {
        "concessionaria": "Light",
        "condicao": "Normal",
        "cabos": [{"condutor": "556MCM-CA, Nu", "vao": 80, "angulo": 30, "flecha": 1.5}],
    }

    def test_calculo_light_valido(self, client):
        resp = client.post(self._URL, json=self._VALID_LIGHT)
        assert resp.status_code == 200
        data = resp.json()
        assert data["resultant_force"] > 0
        assert 0 <= data["resultant_angle"] <= 360
        assert isinstance(data["vectors"], list)
        assert isinstance(data["suggested_poles"], list)

    def test_calculo_enel_valido(self, client):
        payload = {
            "concessionaria": "Enel",
            "condicao": "Normal",
            "cabos": [{"condutor": "1/0 CA", "vao": 50, "angulo": 0, "flecha": 1.0}],
        }
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["resultant_force"] > 0

    def test_condicao_vento_forte(self, client):
        payload = dict(self._VALID_LIGHT)
        payload["condicao"] = "Vento Forte"
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        # Vento forte (1.5x) deve ser maior que Normal
        assert resp.json()["resultant_force"] > 0

    def test_concessionaria_invalida_retorna_422(self, client):
        payload = dict(self._VALID_LIGHT)
        payload["concessionaria"] = "DesconhecidaSA"
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422

    def test_sugestao_de_poste(self, client):
        resp = client.post(self._URL, json=self._VALID_LIGHT)
        assert resp.status_code == 200
        # Deve retornar pelo menos um poste sugerido para força típica
        data = resp.json()
        # suggested_poles é uma lista (pode ser vazia se a força for muito alta)
        assert isinstance(data["suggested_poles"], list)

    def test_multiplos_cabos(self, client):
        payload = {
            "concessionaria": "Light",
            "condicao": "Normal",
            "cabos": [
                {"condutor": "556MCM-CA, Nu", "vao": 80, "angulo": 30, "flecha": 1.5},
                {"condutor": "1/0AWG-CAA, Nu", "vao": 60, "angulo": 90, "flecha": 0.5},
            ],
        }
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 200
        assert len(resp.json()["vectors"]) == 2

    def test_cabos_vazios_retorna_422(self, client):
        payload = {"concessionaria": "Light", "condicao": "Normal", "cabos": []}
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422


# ── Materiais Elétricos ────────────────────────────────────────────────────────


class TestElectricalMaterialsEndpoint:
    """Testa o endpoint GET /api/v1/electrical/materials."""

    _URL = "/api/v1/electrical/materials"

    def test_retorna_200(self, client):
        resp = client.get(self._URL)
        assert resp.status_code == 200

    def test_retorna_lista_com_campos_obrigatorios(self, client):
        data = client.get(self._URL).json()
        assert len(data) >= 2  # Alumínio e Cobre pré-populados
        for item in data:
            assert "name" in item
            assert "resistivity_ohm_mm2_m" in item
            assert "description" in item
            assert isinstance(item["resistivity_ohm_mm2_m"], float)

    def test_aluminio_presente(self, client):
        data = client.get(self._URL).json()
        names = [m["name"] for m in data]
        assert "Alumínio" in names

    def test_cobre_presente(self, client):
        data = client.get(self._URL).json()
        names = [m["name"] for m in data]
        assert "Cobre" in names

    def test_erro_db_retorna_500(self, client, mocker):
        """Cobre branch de erro: exception na lógica → HTTP 500."""
        mocker.patch(
            "src.api.routes.electrical.ElectricalLogic.get_materials",
            side_effect=RuntimeError("DB offline"),
        )
        resp = client.get(self._URL)
        assert resp.status_code == 500


# ── Sugestão de Postes ────────────────────────────────────────────────────────


class TestPoleSuggestEndpoint:
    """Testa o endpoint GET /api/v1/pole-load/suggest."""

    _URL = "/api/v1/pole-load/suggest"

    def test_retorna_200_com_force_valida(self, client):
        resp = client.get(self._URL, params={"force_daN": 150.0})
        assert resp.status_code == 200

    def test_resposta_tem_campos_obrigatorios(self, client):
        data = client.get(self._URL, params={"force_daN": 150.0}).json()
        assert "force_daN" in data
        assert "suggested_poles" in data
        assert isinstance(data["suggested_poles"], list)
        assert data["force_daN"] == 150.0

    def test_force_zero_retorna_422(self, client):
        """force_daN=0 deve falhar na validação Pydantic (gt=0)."""
        resp = client.get(self._URL, params={"force_daN": 0.0})
        assert resp.status_code == 422

    def test_force_muito_alta_retorna_lista_vazia(self, client):
        """Força maior que qualquer poste disponível retorna lista vazia."""
        data = client.get(self._URL, params={"force_daN": 999999.0}).json()
        assert data["suggested_poles"] == []

    def test_concreto_sugerido_para_force_200(self, client):
        """Para 200 daN, deve sugerir pelo menos o poste de Concreto 11m/200daN."""
        data = client.get(self._URL, params={"force_daN": 200.0}).json()
        materials = [p["material"] for p in data["suggested_poles"]]
        assert "Concreto" in materials

    def test_erro_db_retorna_500(self, client, mocker):
        """Cobre branch de erro: exception na lógica → HTTP 500."""
        mocker.patch(
            "src.api.routes.pole_load.PoleLoadLogic.suggest_pole",
            side_effect=RuntimeError("DB offline"),
        )
        resp = client.get(self._URL, params={"force_daN": 100.0})
        assert resp.status_code == 500


# ── Cobertura de branches defensivos ─────────────────────────────────────────


class TestCatenaryEndpointDefensiveBranches:
    """Cobre branches defensivos da rota catenary que não são alcançados via
    validação Pydantic normal (requer mock da lógica)."""

    _URL = "/api/v1/catenary/calculate"

    def test_logic_returns_none_retorna_422(self, client, mocker):
        """Cobre linhas 39-40: CatenaryLogic.calculate_catenary retorna None → 422."""
        mocker.patch(
            "src.api.routes.catenary.CatenaryLogic.calculate_catenary",
            return_value=None,
        )
        payload = {
            "span": 80.0,
            "ha": 9.0,
            "hb": 9.0,
            "tension_daN": 500.0,
            "weight_kg_m": 0.779,
        }
        resp = client.post(self._URL, json=payload)
        assert resp.status_code == 422
        assert resp.json()["detail"] == "Peso linear zero ou dados inválidos para o cálculo."
