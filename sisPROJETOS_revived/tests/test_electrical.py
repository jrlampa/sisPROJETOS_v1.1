"""
Testes do módulo electrical (Dimensionamento Elétrico).
"""

import pytest
from src.modules.electrical.logic import ElectricalLogic


class TestElectricalLogic:
    """Suite de testes para ElectricalLogic."""
    
    @pytest.fixture
    def electrical(self):
        """Fixture que retorna uma instância de ElectricalLogic."""
        return ElectricalLogic()
    
    def test_get_resistivity_aluminum(self, electrical):
        """Testa obtenção de resistividade do alumínio."""
        rho = electrical.get_resistivity('Alumínio')
        assert rho > 0
        assert isinstance(rho, float)
    
    def test_get_resistivity_copper(self, electrical):
        """Testa obtenção de resistividade do cobre."""
        rho = electrical.get_resistivity('Cobre')
        assert rho > 0
        assert isinstance(rho, float)
    
    def test_get_resistivity_unknown_material(self, electrical):
        """Testa resistividade padrão para material desconhecido."""
        rho = electrical.get_resistivity('MaterialInexistente')
        assert rho == 0.0282  # Default alumínio
    
    def test_calculate_voltage_drop_three_phase_valid(self, electrical):
        """Testa cálculo de queda de tensão trifásico com valores válidos."""
        result = electrical.calculate_voltage_drop(
            power_kw=100,
            distance_m=200,
            voltage_v=380,
            material='Alumínio',
            section_mm2=50,
            cos_phi=0.92,
            phases=3
        )
        
        assert result is not None
        assert 'current' in result
        assert 'delta_v_volts' in result
        assert 'percentage_drop' in result
        assert 'allowed' in result
        
        assert result['current'] > 0
        assert result['delta_v_volts'] > 0
        assert result['percentage_drop'] > 0
        assert isinstance(result['allowed'], bool)
    
    def test_calculate_voltage_drop_single_phase_valid(self, electrical):
        """Testa cálculo de queda de tensão monofásico."""
        result = electrical.calculate_voltage_drop(
            power_kw=10,
            distance_m=50,
            voltage_v=220,
            material='Cobre',
            section_mm2=10,
            cos_phi=0.95,
            phases=1
        )
        
        assert result is not None
        assert result['current'] > 0
        assert result['delta_v_volts'] > 0
        assert result['percentage_drop'] >= 0
    
    def test_calculate_voltage_drop_within_limit(self, electrical):
        """Testa que queda de tensão pequena está dentro do limite."""
        result = electrical.calculate_voltage_drop(
            power_kw=5,
            distance_m=10,
            voltage_v=380,
            material='Cobre',
            section_mm2=25,
            cos_phi=0.92,
            phases=3
        )
        
        assert result is not None
        assert result['percentage_drop'] <= 5.0
        assert result['allowed'] is True
    
    def test_calculate_voltage_drop_exceeds_limit(self, electrical):
        """Testa que queda de tensão excessiva excede o limite."""
        result = electrical.calculate_voltage_drop(
            power_kw=500,
            distance_m=1000,
            voltage_v=220,
            material='Alumínio',
            section_mm2=4,
            cos_phi=0.85,
            phases=1
        )
        
        assert result is not None
        assert result['percentage_drop'] > 5.0
        assert result['allowed'] is False
    
    def test_calculate_voltage_drop_invalid_power(self, electrical):
        """Testa cálculo com potência inválida."""
        result = electrical.calculate_voltage_drop(
            power_kw='invalid',
            distance_m=100,
            voltage_v=380,
            material='Alumínio',
            section_mm2=25,
            cos_phi=0.92,
            phases=3
        )
        
        assert result is None
    
    def test_calculate_voltage_drop_zero_section(self, electrical):
        """Testa cálculo com seção zero (divisão por zero)."""
        result = electrical.calculate_voltage_drop(
            power_kw=100,
            distance_m=200,
            voltage_v=380,
            material='Alumínio',
            section_mm2=0,
            cos_phi=0.92,
            phases=3
        )
        
        assert result is None
    
    def test_calculate_voltage_drop_zero_voltage(self, electrical):
        """Testa cálculo com tensão zero."""
        result = electrical.calculate_voltage_drop(
            power_kw=100,
            distance_m=200,
            voltage_v=0,
            material='Alumínio',
            section_mm2=50,
            cos_phi=0.92,
            phases=3
        )
        
        assert result is None
    
    def test_calculate_voltage_drop_negative_distance(self, electrical):
        """Testa cálculo com distância negativa."""
        result = electrical.calculate_voltage_drop(
            power_kw=100,
            distance_m=-200,
            voltage_v=380,
            material='Alumínio',
            section_mm2=50,
            cos_phi=0.92,
            phases=3
        )
        
        # Pode retornar resultado negativo ou None, ambos aceitáveis
        # O importante é não crashar
        assert result is None or result['delta_v_volts'] < 0
    
    def test_calculate_voltage_drop_high_cos_phi(self, electrical):
        """Testa cálculo com fator de potência alto."""
        result = electrical.calculate_voltage_drop(
            power_kw=50,
            distance_m=100,
            voltage_v=380,
            material='Cobre',
            section_mm2=35,
            cos_phi=0.98,
            phases=3
        )
        
        assert result is not None
        assert result['percentage_drop'] > 0
    
    def test_calculate_voltage_drop_low_cos_phi(self, electrical):
        """Testa cálculo com fator de potência baixo."""
        result = electrical.calculate_voltage_drop(
            power_kw=50,
            distance_m=100,
            voltage_v=380,
            material='Alumínio',
            section_mm2=35,
            cos_phi=0.7,
            phases=3
        )
        
        assert result is not None
        assert result['percentage_drop'] > 0
    
    def test_calculate_voltage_drop_current_calculation(self, electrical):
        """Testa se a corrente é calculada corretamente."""
        power = 100  # kW
        voltage = 380  # V
        cos_phi = 0.92
        
        result = electrical.calculate_voltage_drop(
            power_kw=power,
            distance_m=100,
            voltage_v=voltage,
            material='Alumínio',
            section_mm2=50,
            cos_phi=cos_phi,
            phases=3
        )
        
        import math
        expected_current = (power * 1000) / (math.sqrt(3) * voltage * cos_phi)
        
        assert result is not None
        assert abs(result['current'] - expected_current) < 0.01
    
    def test_electrical_logic_has_db_connection(self, electrical):
        """Testa que ElectricalLogic tem conexão com database."""
        assert hasattr(electrical, 'db')
        assert electrical.db is not None
    
    def test_multiple_calculations_consistency(self, electrical):
        """Testa consistência entre múltiplos cálculos."""
        params = {
            'power_kw': 75,
            'distance_m': 150,
            'voltage_v': 380,
            'material': 'Alumínio',
            'section_mm2': 35,
            'cos_phi': 0.92,
            'phases': 3
        }
        
        result1 = electrical.calculate_voltage_drop(**params)
        result2 = electrical.calculate_voltage_drop(**params)
        
        assert result1 == result2
        assert result1['current'] == result2['current']
        assert result1['percentage_drop'] == result2['percentage_drop']
    
    def test_voltage_drop_proportional_to_distance(self, electrical):
        """Testa que queda de tensão é proporcional à distância."""
        base_params = {
            'power_kw': 50,
            'voltage_v': 380,
            'material': 'Alumínio',
            'section_mm2': 25,
            'cos_phi': 0.92,
            'phases': 3
        }
        
        result_100m = electrical.calculate_voltage_drop(distance_m=100, **base_params)
        result_200m = electrical.calculate_voltage_drop(distance_m=200, **base_params)
        
        assert result_100m is not None
        assert result_200m is not None
        assert result_200m['percentage_drop'] > result_100m['percentage_drop']
        # Deve ser aproximadamente o dobro
        ratio = result_200m['percentage_drop'] / result_100m['percentage_drop']
        assert 1.9 < ratio < 2.1
    
    def test_voltage_drop_inverse_to_section(self, electrical):
        """Testa que queda de tensão é inversamente proporcional à seção."""
        base_params = {
            'power_kw': 50,
            'distance_m': 100,
            'voltage_v': 380,
            'material': 'Alumínio',
            'cos_phi': 0.92,
            'phases': 3
        }
        
        result_25mm = electrical.calculate_voltage_drop(section_mm2=25, **base_params)
        result_50mm = electrical.calculate_voltage_drop(section_mm2=50, **base_params)
        
        assert result_25mm is not None
        assert result_50mm is not None
        assert result_25mm['percentage_drop'] > result_50mm['percentage_drop']
        # Seção dobrada = queda reduzida pela metade
        ratio = result_25mm['percentage_drop'] / result_50mm['percentage_drop']
        assert 1.9 < ratio < 2.1

    def test_calculate_voltage_drop_invalid_cos_phi_zero(self, electrical):
        """Testa cálculo com fator de potência zero (inválido)."""
        result = electrical.calculate_voltage_drop(
            power_kw=100,
            distance_m=200,
            voltage_v=380,
            material='Alumínio',
            section_mm2=50,
            cos_phi=0,
            phases=3
        )
        assert result is None

    def test_calculate_voltage_drop_invalid_cos_phi_above_one(self, electrical):
        """Testa cálculo com fator de potência acima de 1 (inválido)."""
        result = electrical.calculate_voltage_drop(
            power_kw=100,
            distance_m=200,
            voltage_v=380,
            material='Alumínio',
            section_mm2=50,
            cos_phi=1.5,
            phases=3
        )
        assert result is None

    def test_calculate_voltage_drop_invalid_phases(self, electrical):
        """Testa cálculo com número de fases inválido."""
        result = electrical.calculate_voltage_drop(
            power_kw=100,
            distance_m=200,
            voltage_v=380,
            material='Alumínio',
            section_mm2=50,
            cos_phi=0.92,
            phases=2
        )
        assert result is None

    def test_get_resistivity_db_exception(self, electrical, mocker):
        """Testa fallback quando banco de dados lança exceção."""
        mocker.patch.object(electrical.db, 'get_connection', side_effect=Exception("DB error"))
        rho = electrical.get_resistivity('Alumínio')
        assert rho == 0.0282  # Default fallback

    def test_get_resistivity_aluminum_from_db(self, electrical):
        """Testa que alumínio tem resistividade correta do banco."""
        rho = electrical.get_resistivity('Alumínio')
        assert rho == pytest.approx(0.0282, rel=1e-3)

    def test_get_resistivity_copper_from_db(self, electrical):
        """Testa que cobre tem resistividade correta do banco."""
        rho = electrical.get_resistivity('Cobre')
        assert rho == pytest.approx(0.0175, rel=1e-3)
