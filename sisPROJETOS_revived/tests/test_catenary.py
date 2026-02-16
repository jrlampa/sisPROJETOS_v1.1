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
