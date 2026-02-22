"""
Testes unitários e de integração para endpoints BIM da API REST do sisPROJETOS.

Cobre:
- GET  /api/v1/data/conductors
- GET  /api/v1/data/poles
- GET  /api/v1/data/concessionaires
- POST /api/v1/converter/kml-to-utm
- POST /api/v1/projects/create
- GET  /api/v1/projects/list

Nota: POST /api/v1/pole-load/report e POST /api/v1/converter/utm-to-dxf
estão em ``tests/test_api_pole_load.py`` (modularização — regra 500 linhas).
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


# ── Listagem de Projetos ──────────────────────────────────────────────────────


class TestProjectListEndpoint:
    """Testes para GET /api/v1/projects/list."""

    _URL = "/api/v1/projects/list"

    def test_lista_projetos_em_tmp_vazio(self, client):
        """Diretório temporário vazio retorna lista vazia."""
        with tempfile.TemporaryDirectory() as tmpdir:
            resp = client.get(self._URL, params={"base_path": tmpdir})
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] == 0
            assert data["projects"] == []

    def test_lista_projetos_com_subpastas(self, client):
        """Diretório com subpastas retorna seus nomes ordenados."""
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "PROJ_B"))
            os.makedirs(os.path.join(tmpdir, "PROJ_A"))
            resp = client.get(self._URL, params={"base_path": tmpdir})
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] == 2
            assert data["projects"] == ["PROJ_A", "PROJ_B"]  # ordenado

    def test_diretorio_inexistente_retorna_404(self, client):
        """Caminho que não existe retorna 404."""
        resp = client.get(self._URL, params={"base_path": "/nao/existe/jamais/x98z"})
        assert resp.status_code == 404

    def test_null_byte_retorna_422(self, client):
        """Null byte no caminho retorna 422 (proteção contra path traversal)."""
        resp = client.get(self._URL, params={"base_path": "/tmp/\x00malicio"})
        assert resp.status_code == 422

    def test_permission_error_retorna_403(self, client, mocker):
        """PermissionError ao listar diretório retorna 403."""
        mocker.patch("api.routes.project_creator.Path.iterdir", side_effect=PermissionError("acesso negado"))
        with tempfile.TemporaryDirectory() as tmpdir:
            resp = client.get(self._URL, params={"base_path": tmpdir})
            assert resp.status_code == 403

    def test_oserror_retorna_500(self, client, mocker):
        """OSError genérico ao listar diretório retorna 500."""
        mocker.patch("api.routes.project_creator.Path.iterdir", side_effect=OSError("disco cheio"))
        with tempfile.TemporaryDirectory() as tmpdir:
            resp = client.get(self._URL, params={"base_path": tmpdir})
            assert resp.status_code == 500
