import pytest
from src.modules.pole_load.logic import PoleLoadLogic

def test_pole_load_resultant_basic():
    logic = PoleLoadLogic()
    inputs = [
        {'rede': 'Convencional', 'condutor': '1/0AWG-CAA, Nu', 'vao': 40, 'angulo': 0, 'flecha': 1.0},
        {'rede': 'Convencional', 'condutor': '1/0AWG-CAA, Nu', 'vao': 40, 'angulo': 180, 'flecha': 1.0}
    ]
    # Opposite pulls of same force should cancel out
    res = logic.calculate_resultant("Light", "Normal", inputs)
    assert res is not None
    # Use a small tolerance for floating point cancellation
    assert res['resultant_force'] < 2.0 
    assert len(res['vectors']) == 2

def test_pole_load_invalid_concessionaire():
    logic = PoleLoadLogic()
    with pytest.raises(KeyError):
        logic.calculate_resultant("InvalidCorp", "Normal", [])

def test_pole_load_90_degree_pull():
    logic = PoleLoadLogic()
    inputs = [
        {'rede': 'Convencional', 'condutor': '1/0AWG-CAA, Nu', 'vao': 50, 'angulo': 0, 'flecha': 1.0},
        {'rede': 'Convencional', 'condutor': '1/0AWG-CAA, Nu', 'vao': 50, 'angulo': 90, 'flecha': 1.0}
    ]
    res = logic.calculate_resultant("Light", "Normal", inputs)
    assert res['resultant_force'] > 0
    # Angle should be approx 45 degrees
    assert 44 < res['resultant_angle'] < 46

def test_pole_load_enel_method():
    logic = PoleLoadLogic()
    # Use a valid entry that exists in the DADOS_CONCESSIONARIAS[Enel] table
    # According to logic.py: 'BT 3x35+54.6': {'tração_fixa': 136}
    inputs = [
        {'rede': 'BT', 'condutor': 'BT 3x35+54.6', 'vao': 30, 'angulo': 10, 'flecha': 0}
    ]
    res = logic.calculate_resultant("Enel", "Normal", inputs)
    assert res is not None
    assert res['resultant_force'] > 0
    assert res['resultant_force'] == 136.0 # Tricao fixa
