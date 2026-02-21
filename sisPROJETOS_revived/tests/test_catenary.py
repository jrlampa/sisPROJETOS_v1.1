import pytest
import numpy as np
from src.modules.catenaria.logic import CatenaryLogic

def test_catenary_calculation_level_span():
    logic = CatenaryLogic()
    # span=100, ha=10, hb=10, tension=1000, weight=0.5
    res = logic.calculate_catenary(100, 10, 10, 1000, 0.5)
    
    assert res is not None
    assert "sag" in res
    assert "x_vals" in res
    assert "y_vals" in res
    assert len(res["x_vals"]) == 100
    # For level span, sag should be positive
    assert res["sag"] > 0
    # Ends should match HA/HB
    assert np.isclose(res["y_vals"][0], 10)
    assert np.isclose(res["y_vals"][-1], 10)

def test_catenary_zero_weight():
    logic = CatenaryLogic()
    res = logic.calculate_catenary(100, 10, 20, 1000, 0)
    assert res is None

def test_conductor_loading():
    logic = CatenaryLogic()
    names = logic.get_conductor_names()
    assert len(names) > 0
    data = logic.get_conductor_by_name(names[0])
    assert "P_kg_m" in data
    assert "T0_daN" in data

def test_catenary_inclined_span():
    logic = CatenaryLogic()
    # span=100, ha=10, hb=30
    res = logic.calculate_catenary(100, 10, 30, 2000, 0.8)
    assert res is not None
    assert res["y_vals"][0] == 10
    assert res["y_vals"][-1] == 30


# ============================================================
# Testes adicionais para cobertura de branches
# ============================================================

def test_get_conductor_by_name_not_found():
    """Cobre linha 56: retorno None para condutor não encontrado."""
    logic = CatenaryLogic()
    result = logic.get_conductor_by_name("ConductorQueNaoExiste_XYZ")
    assert result is None


def test_load_conductors_db_failure(mocker):
    """Cobre linhas 32-34: exceção ao carregar condutores — lista fica vazia."""
    logic = CatenaryLogic()
    # Mocka o DB para falhar na próxima chamada a load_conductors
    mocker.patch.object(logic.db, "get_connection", side_effect=Exception("DB falhou"))
    logic.load_conductors()
    assert logic.conductors == []


def test_export_dxf_creates_file(tmp_path):
    """Cobre linhas 166-168: export_dxf delega para DXFManager."""
    import os
    import numpy as np

    logic = CatenaryLogic()
    result = logic.calculate_catenary(100, 10, 10, 1000, 0.5)
    assert result is not None

    dxf_path = str(tmp_path / "catenaria_test.dxf")
    logic.export_dxf(dxf_path, result["x_vals"], result["y_vals"], result["sag"])

    assert os.path.exists(dxf_path)
    assert os.path.getsize(dxf_path) > 0
