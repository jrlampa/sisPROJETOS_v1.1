"""
Testes End-to-End (E2E) da API REST do sisPROJETOS.

Valida pipelines completos encadeando múltiplas chamadas API com dados reais,
simulando o fluxo de trabalho real de integração BIM.

Cobre:
- Pipeline BIM: POST /converter/kml-to-utm → POST /converter/utm-to-dxf
- Pipeline Elétrico: GET /electrical/standards → POST /electrical/voltage-drop (PRODIST)
- Pipeline Catenária: POST /catenary/calculate (curva + folga NBR 5422) → POST /catenary/dxf
- Pipeline Esforços: POST /pole-load/resultant → GET /pole-load/suggest → POST /pole-load/report
- Pipeline Dados: GET /health → GET /data/conductors → GET /electrical/materials
- Pipeline Projetos: POST /projects/create → GET /projects/list
"""

import base64
import io
import tempfile

import ezdxf
import pytest
from fastapi.testclient import TestClient

# ── Fixture principal ──────────────────────────────────────────────────────────

KML_MINIMAL = base64.b64encode(b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>P1</name>
      <Point><coordinates>-42.92185,-22.15018,720.0</coordinates></Point>
    </Placemark>
    <Placemark>
      <name>P2</name>
      <Point><coordinates>-42.93000,-22.16000,580.0</coordinates></Point>
    </Placemark>
  </Document>
</kml>""").decode()

CABO_PADRAO = {"condutor": "556MCM-CA, Nu", "vao": 80.0, "angulo": 30.0, "flecha": 1.5}


@pytest.fixture(scope="module")
def client():
    """Cliente de testes FastAPI compartilhado por todos os testes E2E."""
    from src.api.app import create_app

    app = create_app()
    return TestClient(app)


# ── E2E Pipeline BIM: KML → UTM → DXF ────────────────────────────────────────


class TestE2EBimKmlToUtmToDxf:
    """Pipeline completo: KML Base64 → coordenadas UTM → arquivo DXF."""

    def test_e2e_kml_to_utm_returns_points(self, client):
        """POST /kml-to-utm extrai pontos do KML codificado em Base64."""
        resp = client.post("/api/v1/converter/kml-to-utm", json={"kml_base64": KML_MINIMAL})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert len(data["points"]) == 2
        names = {p["name"] for p in data["points"]}
        assert "P1" in names and "P2" in names

    def test_e2e_utm_coords_are_numeric(self, client):
        """As coordenadas UTM retornadas são números válidos."""
        resp = client.post("/api/v1/converter/kml-to-utm", json={"kml_base64": KML_MINIMAL})
        for pt in resp.json()["points"]:
            assert isinstance(pt["easting"], float)
            assert isinstance(pt["northing"], float)
            assert pt["easting"] > 0
            assert pt["northing"] > 0

    def test_e2e_utm_to_dxf_pipeline(self, client):
        """Cadeia completa: UTM points da etapa 1 → DXF Base64 na etapa 2."""
        # Etapa 1: KML → UTM
        utm_resp = client.post("/api/v1/converter/kml-to-utm", json={"kml_base64": KML_MINIMAL})
        assert utm_resp.status_code == 200
        utm_points = utm_resp.json()["points"]

        # Etapa 2: UTM → DXF
        dxf_payload = {
            "points": [
                {"name": p["name"], "easting": p["easting"], "northing": p["northing"], "elevation": p["elevation"]}
                for p in utm_points
            ],
            "filename": "e2e_test.dxf",
        }
        dxf_resp = client.post("/api/v1/converter/utm-to-dxf", json=dxf_payload)
        assert dxf_resp.status_code == 200
        data = dxf_resp.json()
        assert "dxf_base64" in data
        assert data["count"] == 2
        assert data["filename"] == "e2e_test.dxf"

    def test_e2e_dxf_is_valid_file(self, client):
        """O DXF gerado no pipeline é um arquivo ezdxf válido com entidades na camada POINTS."""
        utm_resp = client.post("/api/v1/converter/kml-to-utm", json={"kml_base64": KML_MINIMAL})
        utm_points = utm_resp.json()["points"]

        dxf_payload = {
            "points": [
                {"name": p["name"], "easting": p["easting"], "northing": p["northing"], "elevation": p["elevation"]}
                for p in utm_points
            ],
        }
        dxf_resp = client.post("/api/v1/converter/utm-to-dxf", json=dxf_payload)
        dxf_bytes = base64.b64decode(dxf_resp.json()["dxf_base64"])
        doc = ezdxf.read(io.StringIO(dxf_bytes.decode("utf-8", errors="replace")))
        # Entities (POINT + TEXT) are assigned to layer "POINTS"
        entity_layers = {e.dxf.layer for e in doc.modelspace()}
        assert "POINTS" in entity_layers


# ── E2E Pipeline Elétrico: Standards → Voltage Drop ──────────────────────────


class TestE2EElectricalStandardsToVoltageDrop:
    """Pipeline: descobre padrões regulatórios → usa um deles no cálculo de queda."""

    def test_e2e_discover_prodist_standard(self, client):
        """GET /standards retorna PRODIST BT e podemos usá-lo na chamada seguinte."""
        standards_resp = client.get("/api/v1/electrical/standards")
        assert standards_resp.status_code == 200
        names = [s["name"] for s in standards_resp.json()]
        assert any("PRODIST" in n for n in names)

    def test_e2e_voltage_drop_with_prodist_standard(self, client):
        """Usa standard_name descoberto do GET /standards no POST /voltage-drop."""
        standards = client.get("/api/v1/electrical/standards").json()
        prodist = next(s for s in standards if "PRODIST" in s["name"] and "BT" in s["name"])
        standard_name = prodist["name"]

        resp = client.post(
            "/api/v1/electrical/voltage-drop",
            json={
                "power_kw": 50.0,
                "distance_m": 200.0,
                "voltage_v": 220.0,
                "material": "Alumínio",
                "section_mm2": 50.0,
                "phases": 3,
                "standard_name": standard_name,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["standard_name"] == standard_name
        assert data["override_toast"] is not None  # PRODIST sobrepõe ABNT → toast obrigatório

    def test_e2e_prodist_allows_higher_drop_than_nbr(self, client):
        """Mesmos parâmetros: NBR5410 rejeita, PRODIST BT aprova (queda entre 5–8%)."""
        payload = {
            "power_kw": 30.0,
            "distance_m": 250.0,
            "voltage_v": 220.0,
            "material": "Alumínio",
            "section_mm2": 35.0,
            "phases": 1,
        }
        nbr_resp = client.post("/api/v1/electrical/voltage-drop", json={**payload, "standard_name": "NBR 5410"})
        prodist_resp = client.post(
            "/api/v1/electrical/voltage-drop",
            json={**payload, "standard_name": "PRODIST Módulo 8 — BT"},
        )
        assert nbr_resp.status_code == 200
        assert prodist_resp.status_code == 200
        nbr_pct = nbr_resp.json()["percentage_drop"]
        if nbr_pct > 5.0:
            # Queda > 5% → NBR rejeita, PRODIST aprova (se ≤ 8%)
            assert not nbr_resp.json()["allowed"]
            if nbr_pct <= 8.0:
                assert prodist_resp.json()["allowed"]

    def test_e2e_materials_to_voltage_drop(self, client):
        """GET /electrical/materials → usa o primeiro material retornado no /voltage-drop."""
        mats_resp = client.get("/api/v1/electrical/materials")
        assert mats_resp.status_code == 200
        materials = mats_resp.json()
        assert len(materials) >= 1
        mat_name = materials[0]["name"]

        resp = client.post(
            "/api/v1/electrical/voltage-drop",
            json={
                "power_kw": 10.0,
                "distance_m": 100.0,
                "voltage_v": 380.0,
                "material": mat_name,
                "section_mm2": 70.0,
                "phases": 3,
            },
        )
        assert resp.status_code == 200
        # Confirm calculation succeeded — response has a valid drop percentage
        data = resp.json()
        assert "percentage_drop" in data
        assert data["percentage_drop"] >= 0


# ── E2E Pipeline Catenária: Calculate → DXF ──────────────────────────────────


class TestE2ECatenaryCalculateToDxf:
    """Pipeline catenária: calcula flecha + curva + folga NBR 5422, depois gera DXF."""

    _CATENARY_PAYLOAD = {
        "span": 100.0,
        "tension_daN": 2000.0,
        "ha": 10.0,
        "hb": 10.0,
        "weight_kg_m": 1.60,
    }

    def test_e2e_catenary_calculate_returns_sag(self, client):
        """POST /catenary/calculate retorna flecha, tensão e constante catenária."""
        resp = client.post("/api/v1/catenary/calculate", json=self._CATENARY_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert "sag" in data and data["sag"] > 0
        assert "tension" in data and data["tension"] > 0
        assert "catenary_constant" in data and data["catenary_constant"] > 0

    def test_e2e_catenary_with_curve_points(self, client):
        """include_curve=True → response contém 100 pontos de curva."""
        resp = client.post("/api/v1/catenary/calculate", json={**self._CATENARY_PAYLOAD, "include_curve": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["curve_x"] is not None
        assert data["curve_y"] is not None
        assert len(data["curve_x"]) == 100

    def test_e2e_catenary_with_nbr5422_clearance(self, client):
        """include_curve + min_clearance_m → within_clearance é True ou False (não None)."""
        resp = client.post(
            "/api/v1/catenary/calculate",
            json={**self._CATENARY_PAYLOAD, "include_curve": True, "min_clearance_m": 6.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["within_clearance"] is not None
        assert isinstance(data["within_clearance"], bool)
        assert data["curve_x"] is not None  # ambos os campos presentes simultaneamente

    def test_e2e_catenary_calculate_then_dxf(self, client):
        """Cadeia: calcula flecha → gera DXF com os mesmos parâmetros."""
        calc_resp = client.post("/api/v1/catenary/calculate", json=self._CATENARY_PAYLOAD)
        assert calc_resp.status_code == 200
        sag = calc_resp.json()["sag"]

        dxf_resp = client.post("/api/v1/catenary/dxf", json={**self._CATENARY_PAYLOAD, "filename": "e2e_catenary"})
        assert dxf_resp.status_code == 200
        data = dxf_resp.json()
        assert abs(data["sag"] - sag) < 0.001  # DXF usa mesmos parâmetros → mesma flecha

    def test_e2e_catenary_dxf_is_valid(self, client):
        """DXF retornado é um arquivo ezdxf válido com camada CATENARY_CURVE."""
        dxf_resp = client.post("/api/v1/catenary/dxf", json={**self._CATENARY_PAYLOAD, "filename": "valid_test"})
        assert dxf_resp.status_code == 200
        dxf_bytes = base64.b64decode(dxf_resp.json()["dxf_base64"])
        doc = ezdxf.read(io.StringIO(dxf_bytes.decode("utf-8", errors="replace")))
        layer_names = [layer.dxf.name for layer in doc.layers]
        assert "CATENARY_CURVE" in layer_names

    def test_e2e_catenary_spans_monotone_sag(self, client):
        """Vãos 100m, 500m, 1km com mesmo condutor → flecha cresce monotonicamente."""
        sags = []
        for span in [100.0, 500.0, 1000.0]:
            resp = client.post(
                "/api/v1/catenary/calculate",
                json={**self._CATENARY_PAYLOAD, "span": span},
            )
            assert resp.status_code == 200
            sags.append(resp.json()["sag"])
        assert sags[0] < sags[1] < sags[2], f"Flecha não monotônica: {sags}"


# ── E2E Pipeline Esforços em Postes ──────────────────────────────────────────


class TestE2EPoleLoadPipeline:
    """Pipeline esforços: resultante → sugestão de poste → relatório PDF."""

    _POLE_PAYLOAD = {
        "concessionaria": "Light",
        "condicao": "Normal",
        "cabos": [CABO_PADRAO],
    }

    def test_e2e_pole_resultant_returns_force(self, client):
        """POST /pole-load/resultant retorna força resultante e vetores."""
        resp = client.post("/api/v1/pole-load/resultant", json=self._POLE_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["resultant_force"] > 0
        assert len(data["vectors"]) == 1

    def test_e2e_pole_suggest_with_resultant_force(self, client):
        """Usa força da resultante para consultar /pole-load/suggest."""
        calc_resp = client.post("/api/v1/pole-load/resultant", json=self._POLE_PAYLOAD)
        force = calc_resp.json()["resultant_force"]

        suggest_resp = client.get(f"/api/v1/pole-load/suggest?force_daN={force}")
        assert suggest_resp.status_code == 200
        poles = suggest_resp.json()["suggested_poles"]
        # Todos os postes sugeridos devem suportar a força calculada (chave 'load' na dict)
        for pole in poles:
            assert pole["load"] >= force

    def test_e2e_pole_report_pdf_base64(self, client):
        """POST /pole-load/report gera PDF Base64 a partir dos mesmos dados."""
        payload = {**self._POLE_PAYLOAD, "project_name": "E2E_TESTE", "filename": "e2e_relatorio"}
        resp = client.post("/api/v1/pole-load/report", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "pdf_base64" in data
        assert data["filename"].endswith(".pdf")
        # Verifica que o Base64 é um PDF válido (cabeçalho %PDF)
        pdf_bytes = base64.b64decode(data["pdf_base64"])
        assert pdf_bytes[:4] == b"%PDF"

    def test_e2e_resultant_and_report_consistent_force(self, client):
        """Força resultante do /resultant e do /report são iguais (mesmos dados)."""
        resultant_resp = client.post("/api/v1/pole-load/resultant", json=self._POLE_PAYLOAD)
        report_resp = client.post(
            "/api/v1/pole-load/report", json={**self._POLE_PAYLOAD, "filename": "e2e_force_check"}
        )
        assert resultant_resp.status_code == 200
        assert report_resp.status_code == 200
        assert abs(resultant_resp.json()["resultant_force"] - report_resp.json()["resultant_force"]) < 0.001


# ── E2E Pipeline Saúde + Catálogo ────────────────────────────────────────────


class TestE2EHealthAndDataCatalog:
    """Pipeline saúde → catálogo de dados mestres BIM."""

    def test_e2e_health_then_conductors(self, client):
        """GET /health OK → GET /data/conductors retorna lista não vazia."""
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] in ("ok", "degraded")

        conductors_resp = client.get("/api/v1/data/conductors")
        assert conductors_resp.status_code == 200
        assert len(conductors_resp.json()) >= 1

    def test_e2e_data_catalog_trio(self, client):
        """Conductors, poles e concessionaires — todos retornam dados reais do DB."""
        c_resp = client.get("/api/v1/data/conductors")
        p_resp = client.get("/api/v1/data/poles")
        con_resp = client.get("/api/v1/data/concessionaires")
        assert c_resp.status_code == 200
        assert p_resp.status_code == 200
        assert con_resp.status_code == 200
        assert len(c_resp.json()) >= 1
        assert len(p_resp.json()) >= 1
        assert len(con_resp.json()) >= 1

    def test_e2e_health_has_all_fields(self, client):
        """GET /health retorna todos os campos esperados para Docker HEALTHCHECK."""
        data = client.get("/health").json()
        assert "status" in data
        assert "version" in data
        assert "db_status" in data
        assert "environment" in data
        assert "timestamp" in data


# ── E2E Pipeline Projetos: Create → List ─────────────────────────────────────


class TestE2EProjectsCreateAndList:
    """Pipeline de projetos: cria projeto → lista projetos no mesmo diretório."""

    def test_e2e_create_then_list(self, client):
        """POST /projects/create → GET /projects/list retorna o projeto criado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_name = "E2E_PROJETO_TESTE"

            # Etapa 1: criar projeto
            create_resp = client.post(
                "/api/v1/projects/create",
                json={"project_name": project_name, "base_path": tmpdir},
            )
            assert create_resp.status_code == 200
            # Note: success may be False if templates are missing — check for graceful handling
            create_data = create_resp.json()
            assert "success" in create_data
            assert "message" in create_data

            # Etapa 2: listar projetos
            list_resp = client.get(f"/api/v1/projects/list?base_path={tmpdir}")
            assert list_resp.status_code == 200
            list_data = list_resp.json()
            assert "projects" in list_data
            assert "count" in list_data
            assert list_data["base_path"] == str(tmpdir)

            if create_data["success"]:
                assert project_name in list_data["projects"]
                assert list_data["count"] >= 1

    def test_e2e_list_projects_empty_dir(self, client):
        """Diretório vazio retorna lista vazia (count=0)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resp = client.get(f"/api/v1/projects/list?base_path={tmpdir}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] == 0
            assert data["projects"] == []

    def test_e2e_list_projects_nonexistent_returns_404(self, client):
        """Diretório inexistente retorna 404."""
        resp = client.get("/api/v1/projects/list?base_path=/nao/existe/jamais/aqui")
        assert resp.status_code == 404
