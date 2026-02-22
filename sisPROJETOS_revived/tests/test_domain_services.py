"""
Testes para serviços de domínio (DDD Domain Services) e interfaces de
repositório (DDD Ports) do sisPROJETOS.

Verifica:
    - CatenaryDomainService: fórmula catenária, invariantes, imutabilidade do resultado
    - VoltageDropDomainService: fórmula queda de tensão, is_within_limit, validações
    - ConductorRepository / PoleRepository / ConcessionaireRepository:
        isinstance checks com implementações in-memory (stubs)
"""

import math

import pytest

from domain.entities import Concessionaire, Conductor, Pole
from domain.repositories import ConcessionaireRepository, ConductorRepository, PoleRepository
from domain.services import CatenaryDomainService, VoltageDropDomainService
from domain.value_objects import CatenaryResult, VoltageDropResult

# ─── Stubs in-memory para os Protocols ────────────────────────────────────────


class _InMemoryConductorRepo:
    """Implementação stub in-memory para verificar o Protocol ConductorRepository."""

    def __init__(self) -> None:
        self._data = [
            Conductor(name="556MCM-CA", weight_kg_m=1.594, breaking_load_daN=13750.0),
            Conductor(name="1/0AWG-CAA", weight_kg_m=0.455, breaking_load_daN=3560.0),
        ]

    def get_all(self):
        return list(self._data)

    def get_by_name(self, name: str):
        return next((c for c in self._data if c.name == name), None)


class _InMemoryPoleRepo:
    """Implementação stub in-memory para verificar o Protocol PoleRepository."""

    def __init__(self) -> None:
        self._data = [
            Pole(material="Concreto", height_m=11.0, format="Circular", nominal_load_daN=150.0),
            Pole(material="Concreto", height_m=11.0, format="Circular", nominal_load_daN=300.0),
            Pole(material="Concreto", height_m=11.0, format="Circular", nominal_load_daN=600.0),
        ]

    def get_all(self):
        return list(self._data)

    def suggest_by_force(self, force_daN: float):
        return sorted(
            [p for p in self._data if p.nominal_load_daN >= force_daN],
            key=lambda p: p.nominal_load_daN,
        )


class _InMemoryConcessionaireRepo:
    """Implementação stub in-memory para verificar o Protocol ConcessionaireRepository."""

    def __init__(self) -> None:
        self._data = [
            Concessionaire(name="Light", method="flecha"),
            Concessionaire(name="Enel", method="tabela"),
        ]

    def get_all(self):
        return list(self._data)

    def get_by_name(self, name: str):
        return next((c for c in self._data if c.name == name), None)


# ─── CatenaryDomainService ────────────────────────────────────────────────────


class TestCatenaryDomainService:
    def setup_method(self) -> None:
        self.svc = CatenaryDomainService()
        self.conductor = Conductor(name="556MCM-CA", weight_kg_m=1.594, breaking_load_daN=13750.0)

    def test_calculate_returns_catenary_result(self):
        """Retorna instância de CatenaryResult."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        assert isinstance(result, CatenaryResult)

    def test_calculate_sag_positive(self):
        """Flecha calculada é positiva para condutor real."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        assert result.sag > 0

    def test_calculate_tension_preserved(self):
        """Tensão no resultado é igual à tensão de entrada."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        assert result.tension == 2000.0

    def test_catenary_constant_formula(self):
        """Constante catenária a = T / w_daN/m (NBR 5422 §3.2)."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        w_dan_m = self.conductor.weight_kg_m * 0.980665
        expected_a = 2000.0 / w_dan_m
        assert abs(result.catenary_constant - round(expected_a, 6)) < 0.01

    def test_sag_hyperbolic_formula(self):
        """Flecha segue f = a·(cosh(L/2a)−1) conforme NBR 5422."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        w = self.conductor.weight_kg_m * 0.980665
        a = 2000.0 / w
        expected_sag = a * (math.cosh(100.0 / (2 * a)) - 1)
        assert abs(result.sag - expected_sag) < 0.001

    def test_larger_span_gives_larger_sag(self):
        """Vãos maiores produzem flechas maiores para o mesmo condutor e tensão."""
        r100 = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        r500 = self.svc.calculate(self.conductor, span=500.0, tension_daN=2000.0)
        r1000 = self.svc.calculate(self.conductor, span=1000.0, tension_daN=2000.0)
        assert r100.sag < r500.sag < r1000.sag

    def test_higher_tension_gives_smaller_sag(self):
        """Tensões maiores reduzem a flecha para o mesmo condutor e vão."""
        r_low = self.svc.calculate(self.conductor, span=100.0, tension_daN=1000.0)
        r_high = self.svc.calculate(self.conductor, span=100.0, tension_daN=4000.0)
        assert r_low.sag > r_high.sag

    def test_result_is_immutable(self):
        """CatenaryResult é imutável (frozen dataclass)."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        with pytest.raises((TypeError, AttributeError)):
            result.sag = 99.9  # type: ignore[misc]

    def test_invalid_span_zero(self):
        """span = 0 levanta ValueError."""
        with pytest.raises(ValueError, match="Vão deve ser positivo"):
            self.svc.calculate(self.conductor, span=0.0, tension_daN=2000.0)

    def test_invalid_span_negative(self):
        """span negativo levanta ValueError."""
        with pytest.raises(ValueError, match="Vão deve ser positivo"):
            self.svc.calculate(self.conductor, span=-10.0, tension_daN=2000.0)

    def test_invalid_tension_zero(self):
        """tension_daN = 0 levanta ValueError."""
        with pytest.raises(ValueError, match="Tensão deve ser positiva"):
            self.svc.calculate(self.conductor, span=100.0, tension_daN=0.0)

    def test_invalid_tension_negative(self):
        """tension_daN negativa levanta ValueError."""
        with pytest.raises(ValueError, match="Tensão deve ser positiva"):
            self.svc.calculate(self.conductor, span=100.0, tension_daN=-500.0)

    def test_conductor_zero_weight_raises(self):
        """Condutor com weight_kg_m = 0 levanta ValueError."""
        zero_weight = Conductor(name="ZeroWeight", weight_kg_m=0.0, breaking_load_daN=100.0)
        with pytest.raises(ValueError, match="Peso linear do condutor deve ser > 0"):
            self.svc.calculate(zero_weight, span=100.0, tension_daN=2000.0)

    def test_is_within_clearance_true(self):
        """Flecha dentro da folga mínima retorna True."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        assert self.svc.is_within_clearance(result, min_clearance_m=result.sag + 1.0)

    def test_is_within_clearance_equal(self):
        """Flecha exatamente igual à folga mínima retorna True (limite incluído)."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        assert self.svc.is_within_clearance(result, min_clearance_m=result.sag)

    def test_is_within_clearance_false(self):
        """Flecha maior que a folga mínima retorna False."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        assert not self.svc.is_within_clearance(result, min_clearance_m=result.sag - 0.001)

    def test_100m_span_sag_range(self):
        """Vão de 100m com condutor real: flecha plausível (0.1 ≤ f ≤ 5m) per NBR 5422."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        assert 0.1 <= result.sag <= 5.0

    def test_500m_span_sag_range(self):
        """Vão de 500m: flecha maior que 100m e dentro de limite razoável."""
        r100 = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0)
        r500 = self.svc.calculate(self.conductor, span=500.0, tension_daN=2000.0)
        assert r500.sag > r100.sag
        assert r500.sag <= 200.0

    def test_1000m_span_sag_comparison(self):
        """Vão de 1000m: flecha maior que 500m."""
        r500 = self.svc.calculate(self.conductor, span=500.0, tension_daN=2000.0)
        r1000 = self.svc.calculate(self.conductor, span=1000.0, tension_daN=2000.0)
        assert r1000.sag > r500.sag

    def test_ha_hb_default_accepted(self):
        """Parâmetros ha e hb com valores padrão (0.0) são aceitos."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0, ha=0.0, hb=0.0)
        assert result.sag > 0

    def test_ha_hb_nonzero_accepted(self):
        """Parâmetros ha e hb não-zero são aceitos (reservados para extensões futuras)."""
        result = self.svc.calculate(self.conductor, span=100.0, tension_daN=2000.0, ha=10.0, hb=12.0)
        assert isinstance(result, CatenaryResult)


# ─── VoltageDropDomainService ─────────────────────────────────────────────────


class TestVoltageDropDomainService:
    def setup_method(self) -> None:
        self.svc = VoltageDropDomainService()

    def test_calculate_returns_voltage_drop_result(self):
        """Retorna instância de VoltageDropResult."""
        result = self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3)
        assert isinstance(result, VoltageDropResult)

    def test_calculate_three_phase_drop_positive(self):
        """Cálculo trifásico retorna queda de tensão positiva."""
        result = self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3)
        assert result.drop_v > 0
        assert result.drop_percent > 0

    def test_calculate_single_phase_drop_positive(self):
        """Cálculo monofásico retorna queda de tensão positiva."""
        result = self.svc.calculate("Cobre", 0.0172, 50.0, 5.0, 10.0, 220.0, 1)
        assert result.drop_v > 0
        assert result.drop_percent > 0

    def test_material_preserved(self):
        """Material é preservado no resultado."""
        result = self.svc.calculate("Cobre", 0.0172, 100.0, 10.0, 35.0, 380.0, 3)
        assert result.material == "Cobre"

    def test_result_is_immutable(self):
        """VoltageDropResult é imutável (frozen dataclass)."""
        result = self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3)
        with pytest.raises((TypeError, AttributeError)):
            result.drop_v = 99.9  # type: ignore[misc]

    def test_within_limit_passes_nbr5410(self):
        """Queda de tensão ≤ 5% é aprovada pela NBR 5410."""
        # Carga pequena + seção grande → queda mínima
        result = self.svc.calculate("Alumínio", 0.0282, 10.0, 1.0, 95.0, 380.0, 3)
        assert result.is_within_limit

    def test_exceeds_limit_fails_nbr5410(self):
        """Queda de tensão > 5% reprova pela NBR 5410."""
        # Carga alta + seção pequena + distância longa → queda elevada
        result = self.svc.calculate("Alumínio", 0.0282, 1000.0, 100.0, 6.0, 220.0, 1)
        assert not result.is_within_limit

    def test_zero_distance_zero_drop(self):
        """Distância zero resulta em queda de tensão zero."""
        result = self.svc.calculate("Alumínio", 0.0282, 0.0, 10.0, 35.0, 380.0, 3)
        assert result.drop_v == 0.0
        assert result.drop_percent == 0.0

    def test_larger_section_reduces_drop(self):
        """Seção maior reduz a queda de tensão (R ∝ 1/A)."""
        r_small = self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 16.0, 380.0, 3)
        r_large = self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 95.0, 380.0, 3)
        assert r_large.drop_percent < r_small.drop_percent

    def test_invalid_material_empty(self):
        """Material vazio levanta ValueError."""
        with pytest.raises(ValueError, match="Material do condutor é obrigatório"):
            self.svc.calculate("", 0.0282, 100.0, 10.0, 35.0, 380.0, 3)

    def test_invalid_resistivity_zero(self):
        """Resistividade zero levanta ValueError."""
        with pytest.raises(ValueError, match="Resistividade deve ser positiva"):
            self.svc.calculate("Alumínio", 0.0, 100.0, 10.0, 35.0, 380.0, 3)

    def test_invalid_resistivity_negative(self):
        """Resistividade negativa levanta ValueError."""
        with pytest.raises(ValueError, match="Resistividade deve ser positiva"):
            self.svc.calculate("Alumínio", -0.01, 100.0, 10.0, 35.0, 380.0, 3)

    def test_invalid_length_negative(self):
        """Comprimento negativo levanta ValueError."""
        with pytest.raises(ValueError, match="Comprimento não pode ser negativo"):
            self.svc.calculate("Alumínio", 0.0282, -1.0, 10.0, 35.0, 380.0, 3)

    def test_invalid_power_zero(self):
        """Potência zero levanta ValueError."""
        with pytest.raises(ValueError, match="Potência deve ser positiva"):
            self.svc.calculate("Alumínio", 0.0282, 100.0, 0.0, 35.0, 380.0, 3)

    def test_invalid_section_zero(self):
        """Seção transversal zero levanta ValueError."""
        with pytest.raises(ValueError, match="Seção transversal deve ser positiva"):
            self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 0.0, 380.0, 3)

    def test_invalid_voltage_zero(self):
        """Tensão zero levanta ValueError."""
        with pytest.raises(ValueError, match="Tensão deve ser positiva"):
            self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 0.0, 3)

    def test_invalid_phases_two(self):
        """Número de fases inválido (2) levanta ValueError."""
        with pytest.raises(ValueError, match="Fases deve ser 1 ou 3"):
            self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 2)

    def test_invalid_cos_phi_zero(self):
        """Fator de potência zero levanta ValueError."""
        with pytest.raises(ValueError, match="Fator de potência"):
            self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3, cos_phi=0.0)

    def test_invalid_cos_phi_exceeds_one(self):
        """Fator de potência > 1 levanta ValueError."""
        with pytest.raises(ValueError, match="Fator de potência"):
            self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3, cos_phi=1.1)

    def test_cos_phi_exactly_one_accepted(self):
        """Fator de potência exatamente 1.0 é aceito (limite incluído)."""
        result = self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3, cos_phi=1.0)
        assert isinstance(result, VoltageDropResult)


# ─── ConductorRepository Protocol ─────────────────────────────────────────────


class TestConductorRepository:
    def setup_method(self) -> None:
        self.repo = _InMemoryConductorRepo()

    def test_isinstance_protocol(self):
        """Stub in-memory satisfaz o Protocol ConductorRepository."""
        assert isinstance(self.repo, ConductorRepository)

    def test_get_all_returns_list_of_conductors(self):
        """get_all() retorna lista de entidades Conductor."""
        conductors = self.repo.get_all()
        assert isinstance(conductors, list)
        assert all(isinstance(c, Conductor) for c in conductors)

    def test_get_all_count(self):
        """get_all() retorna os 2 condutores do stub."""
        assert len(self.repo.get_all()) == 2

    def test_get_by_name_found(self):
        """get_by_name() encontra condutor existente."""
        c = self.repo.get_by_name("556MCM-CA")
        assert c is not None
        assert c.name == "556MCM-CA"

    def test_get_by_name_not_found(self):
        """get_by_name() retorna None para nome inexistente."""
        assert self.repo.get_by_name("INEXISTENTE") is None

    def test_get_all_returns_copy(self):
        """get_all() retorna lista nova a cada chamada (não referência interna)."""
        list1 = self.repo.get_all()
        list2 = self.repo.get_all()
        assert list1 is not list2


# ─── PoleRepository Protocol ───────────────────────────────────────────────────


class TestPoleRepository:
    def setup_method(self) -> None:
        self.repo = _InMemoryPoleRepo()

    def test_isinstance_protocol(self):
        """Stub in-memory satisfaz o Protocol PoleRepository."""
        assert isinstance(self.repo, PoleRepository)

    def test_get_all_returns_list_of_poles(self):
        """get_all() retorna lista de entidades Pole."""
        poles = self.repo.get_all()
        assert isinstance(poles, list)
        assert all(isinstance(p, Pole) for p in poles)

    def test_suggest_by_force_filters_correctly(self):
        """suggest_by_force() retorna apenas postes com carga >= force_daN."""
        result = self.repo.suggest_by_force(300.0)
        assert all(p.nominal_load_daN >= 300.0 for p in result)

    def test_suggest_by_force_ordered_ascending(self):
        """suggest_by_force() ordena postes por carga nominal crescente."""
        result = self.repo.suggest_by_force(100.0)
        loads = [p.nominal_load_daN for p in result]
        assert loads == sorted(loads)

    def test_suggest_by_force_no_match_returns_empty(self):
        """suggest_by_force() retorna lista vazia quando nenhum poste é adequado."""
        result = self.repo.suggest_by_force(10_000.0)
        assert result == []

    def test_suggest_by_force_all_match(self):
        """suggest_by_force() com force mínima retorna todos os postes."""
        result = self.repo.suggest_by_force(0.0)
        assert len(result) == 3


# ─── ConcessionaireRepository Protocol ────────────────────────────────────────


class TestConcessionaireRepository:
    def setup_method(self) -> None:
        self.repo = _InMemoryConcessionaireRepo()

    def test_isinstance_protocol(self):
        """Stub in-memory satisfaz o Protocol ConcessionaireRepository."""
        assert isinstance(self.repo, ConcessionaireRepository)

    def test_get_all_returns_list_of_concessionaires(self):
        """get_all() retorna lista de entidades Concessionaire."""
        concessionaires = self.repo.get_all()
        assert isinstance(concessionaires, list)
        assert all(isinstance(c, Concessionaire) for c in concessionaires)

    def test_get_all_count(self):
        """get_all() retorna as 2 concessionárias do stub."""
        assert len(self.repo.get_all()) == 2

    def test_get_by_name_light(self):
        """get_by_name() encontra Light com método flecha."""
        c = self.repo.get_by_name("Light")
        assert c is not None
        assert c.method == "flecha"

    def test_get_by_name_enel(self):
        """get_by_name() encontra Enel com método tabela."""
        c = self.repo.get_by_name("Enel")
        assert c is not None
        assert c.method == "tabela"

    def test_get_by_name_not_found(self):
        """get_by_name() retorna None para nome inexistente."""
        assert self.repo.get_by_name("INEXISTENTE") is None
