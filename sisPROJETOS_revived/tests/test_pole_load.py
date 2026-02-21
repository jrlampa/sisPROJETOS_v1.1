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


# ---------------------------------------------------------------------------
# Testes adicionais para cobertura de branches específicos
# ---------------------------------------------------------------------------

def test_get_concessionaires():
    """Testa listagem de concessionárias do banco."""
    logic = PoleLoadLogic()
    concessionaires = logic.get_concessionaires()
    assert isinstance(concessionaires, list)
    assert len(concessionaires) >= 2
    assert "Light" in concessionaires
    assert "Enel" in concessionaires


def test_get_concessionaire_method_light():
    """Testa método de cálculo para Light."""
    logic = PoleLoadLogic()
    method = logic.get_concessionaire_method("Light")
    assert method == "flecha"


def test_get_concessionaire_method_enel():
    """Testa método de cálculo para Enel."""
    logic = PoleLoadLogic()
    method = logic.get_concessionaire_method("Enel")
    assert method == "tabela"


def test_get_concessionaire_method_invalid():
    """Testa erro ao buscar concessionária inválida."""
    logic = PoleLoadLogic()
    with pytest.raises(KeyError):
        logic.get_concessionaire_method("ConcessionariaInexistente")


def test_interpolar_dict_exact_vao():
    """Testa interpolação com vão exato na tabela."""
    logic = PoleLoadLogic()
    tabela = {20: 100, 40: 200, 60: 300}
    assert logic.interpolar(tabela, 40) == 200


def test_interpolar_dict_below_min():
    """Testa interpolação com vão abaixo do mínimo."""
    logic = PoleLoadLogic()
    tabela = {20: 100, 40: 200, 60: 300}
    assert logic.interpolar(tabela, 10) == 100


def test_interpolar_dict_above_max():
    """Testa interpolação com vão acima do máximo."""
    logic = PoleLoadLogic()
    tabela = {20: 100, 40: 200, 60: 300}
    assert logic.interpolar(tabela, 80) == 300


def test_interpolar_dict_between_values():
    """Testa interpolação linear entre dois valores."""
    logic = PoleLoadLogic()
    tabela = {20: 100, 40: 200}
    result = logic.interpolar(tabela, 30)
    assert result == pytest.approx(150.0)


def test_interpolar_non_dict():
    """Testa que não-dicionário retorna 0."""
    logic = PoleLoadLogic()
    assert logic.interpolar(None, 30) == 0
    assert logic.interpolar("not a dict", 30) == 0


def test_interpolar_empty_dict():
    """Testa que dicionário vazio retorna 0."""
    logic = PoleLoadLogic()
    assert logic.interpolar({}, 30) == 0


def test_suggest_pole_returns_list():
    """Testa que suggest_pole retorna lista."""
    logic = PoleLoadLogic()
    result = logic.suggest_pole(100.0)
    assert isinstance(result, list)


def test_suggest_pole_with_low_force():
    """Testa suggest_pole com força baixa — deve retornar opções."""
    logic = PoleLoadLogic()
    result = logic.suggest_pole(1.0)
    assert isinstance(result, list)
    # Cada item deve ter material, description e load
    for item in result:
        assert "material" in item
        assert "description" in item
        assert "load" in item


def test_suggest_pole_with_very_high_force():
    """Testa suggest_pole com força muito alta — pode retornar vazio."""
    logic = PoleLoadLogic()
    result = logic.suggest_pole(99999.0)
    assert isinstance(result, list)


def test_calculate_resultant_negative_angle_wraps():
    """Testa que ângulo resultante negativo é corrigido para [0,360)."""
    logic = PoleLoadLogic()
    # Um cabo com ângulo de 270° e outro com 0° deve gerar resultante com ângulo válido
    inputs = [
        {"rede": "Convencional", "condutor": "1/0AWG-CAA, Nu", "vao": 50, "angulo": 270, "flecha": 1.0},
    ]
    res = logic.calculate_resultant("Light", "Normal", inputs)
    assert 0 <= res["resultant_angle"] <= 360


def test_calculate_resultant_vento_forte():
    """Testa fator de segurança Vento Forte (1.5x)."""
    logic = PoleLoadLogic()
    inputs = [
        {"rede": "Convencional", "condutor": "1/0AWG-CAA, Nu", "vao": 50, "angulo": 0, "flecha": 1.0},
    ]
    res_normal = logic.calculate_resultant("Light", "Normal", inputs)
    res_vento = logic.calculate_resultant("Light", "Vento Forte", inputs)
    assert res_vento["resultant_force"] == pytest.approx(res_normal["resultant_force"] * 1.5)


def test_calculate_resultant_enel_with_interpolation():
    """Testa Enel com condutor sem tração fixa (usa interpolação)."""
    logic = PoleLoadLogic()
    # 1/0 CA usa tabela com vãos (não tração fixa), vão 30m (entre 20 e 40m da DB)
    inputs = [
        {"rede": "Rede MT", "condutor": "1/0 CA", "vao": 30, "angulo": 0, "flecha": 0},
    ]
    res = logic.calculate_resultant("Enel", "Normal", inputs)
    assert res is not None
    assert res["resultant_force"] >= 0
