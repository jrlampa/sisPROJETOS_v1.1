"""
Testes para a camada de domínio DDD do sisPROJETOS.

Verifica value objects e entidades de domínio:
- Criação válida
- Validação de invariantes de negócio em __post_init__
- Imutabilidade de value objects (frozen=True)
- Propriedades calculadas (is_within_limit)
- Regras de negócio (VALID_METHODS, LIMIT_PERCENT)
"""

import pytest

from src.domain.entities import Concessionaire, Conductor, Pole
from src.domain.value_objects import CatenaryResult, SpanResult, UTMCoordinate, VoltageDropResult

# ─── UTMCoordinate ────────────────────────────────────────────────────────────


class TestUTMCoordinate:
    def test_valid_utm_coordinate(self):
        """Coordenada UTM válida é criada com sucesso."""
        p = UTMCoordinate(easting=788547.0, northing=7634925.0, zone="23K")
        assert p.easting == 788547.0
        assert p.northing == 7634925.0
        assert p.zone == "23K"
        assert p.elevation == 0.0  # default

    def test_utm_with_elevation(self):
        """Coordenada UTM com elevação explícita."""
        p = UTMCoordinate(easting=714315.7, northing=7549084.2, zone="23S", elevation=580.0)
        assert p.elevation == 580.0

    def test_utm_is_immutable(self):
        """UTMCoordinate é imutável (frozen dataclass)."""
        p = UTMCoordinate(easting=788547.0, northing=7634925.0, zone="23K")
        with pytest.raises((TypeError, AttributeError)):
            p.easting = 999.0  # type: ignore[misc]

    def test_utm_invalid_easting_zero(self):
        """Easting zero levanta ValueError."""
        with pytest.raises(ValueError, match="Easting deve ser positivo"):
            UTMCoordinate(easting=0.0, northing=7634925.0, zone="23K")

    def test_utm_invalid_easting_negative(self):
        """Easting negativo levanta ValueError."""
        with pytest.raises(ValueError, match="Easting deve ser positivo"):
            UTMCoordinate(easting=-100.0, northing=7634925.0, zone="23K")

    def test_utm_invalid_northing_zero(self):
        """Northing zero levanta ValueError."""
        with pytest.raises(ValueError, match="Northing deve ser positivo"):
            UTMCoordinate(easting=788547.0, northing=0.0, zone="23K")

    def test_utm_invalid_zone_empty(self):
        """Zone vazia levanta ValueError."""
        with pytest.raises(ValueError, match="Zone UTM"):
            UTMCoordinate(easting=788547.0, northing=7634925.0, zone="")

    def test_utm_equality(self):
        """Duas UTMCoordinate com mesmos valores são iguais (value semantics)."""
        p1 = UTMCoordinate(easting=788547.0, northing=7634925.0, zone="23K", elevation=720.0)
        p2 = UTMCoordinate(easting=788547.0, northing=7634925.0, zone="23K", elevation=720.0)
        assert p1 == p2


# ─── CatenaryResult ───────────────────────────────────────────────────────────


class TestCatenaryResult:
    def test_valid_catenary_result(self):
        """CatenaryResult válido é criado com sucesso."""
        r = CatenaryResult(sag=1.23, tension=2000.0, catenary_constant=130.5)
        assert r.sag == 1.23
        assert r.tension == 2000.0
        assert r.catenary_constant == 130.5

    def test_catenary_is_immutable(self):
        """CatenaryResult é imutável."""
        r = CatenaryResult(sag=1.0, tension=2000.0, catenary_constant=100.0)
        with pytest.raises((TypeError, AttributeError)):
            r.sag = 99.0  # type: ignore[misc]

    def test_catenary_sag_zero_valid(self):
        """Flecha zero é válida (condutor teso)."""
        r = CatenaryResult(sag=0.0, tension=2000.0, catenary_constant=100.0)
        assert r.sag == 0.0

    def test_catenary_negative_sag(self):
        """Flecha negativa levanta ValueError."""
        with pytest.raises(ValueError, match="sag.*negativa"):
            CatenaryResult(sag=-1.0, tension=2000.0, catenary_constant=100.0)

    def test_catenary_zero_tension(self):
        """Tensão zero levanta ValueError."""
        with pytest.raises(ValueError, match="Tensão horizontal"):
            CatenaryResult(sag=1.0, tension=0.0, catenary_constant=100.0)

    def test_catenary_zero_catenary_constant(self):
        """Constante catenária zero levanta ValueError."""
        with pytest.raises(ValueError, match="Constante catenária"):
            CatenaryResult(sag=1.0, tension=2000.0, catenary_constant=0.0)


# ─── VoltageDropResult ────────────────────────────────────────────────────────


class TestVoltageDropResult:
    def test_valid_voltage_drop(self):
        """VoltageDropResult válido é criado com sucesso."""
        r = VoltageDropResult(drop_v=5.5, drop_percent=2.5, material="Alumínio")
        assert r.drop_v == 5.5
        assert r.drop_percent == 2.5
        assert r.material == "Alumínio"

    def test_is_within_limit_true(self):
        """Queda ≤ 5% está dentro do limite NBR 5410."""
        r = VoltageDropResult(drop_v=5.5, drop_percent=2.5, material="Alumínio")
        assert r.is_within_limit is True

    def test_is_within_limit_exactly_five(self):
        """Queda exatamente de 5% está no limite (incluso)."""
        r = VoltageDropResult(drop_v=11.0, drop_percent=5.0, material="Cobre")
        assert r.is_within_limit is True

    def test_is_within_limit_false(self):
        """Queda > 5% está acima do limite NBR 5410."""
        r = VoltageDropResult(drop_v=15.0, drop_percent=6.8, material="Cobre")
        assert r.is_within_limit is False

    def test_voltage_drop_is_immutable(self):
        """VoltageDropResult é imutável."""
        r = VoltageDropResult(drop_v=5.0, drop_percent=2.0, material="Alumínio")
        with pytest.raises((TypeError, AttributeError)):
            r.drop_v = 99.0  # type: ignore[misc]

    def test_negative_drop_v_raises(self):
        """Queda negativa em Volts levanta ValueError."""
        with pytest.raises(ValueError, match="Queda de tensão não pode ser negativa"):
            VoltageDropResult(drop_v=-1.0, drop_percent=2.0, material="Alumínio")

    def test_negative_drop_percent_raises(self):
        """Porcentagem negativa levanta ValueError."""
        with pytest.raises(ValueError, match="Porcentagem de queda"):
            VoltageDropResult(drop_v=1.0, drop_percent=-0.1, material="Alumínio")

    def test_empty_material_raises(self):
        """Material vazio levanta ValueError."""
        with pytest.raises(ValueError, match="Material do condutor"):
            VoltageDropResult(drop_v=5.0, drop_percent=2.0, material="")

    def test_limit_percent_is_class_variable(self):
        """LIMIT_PERCENT é uma class variable, não um campo de instância."""
        assert VoltageDropResult.LIMIT_PERCENT == 5.0
        r = VoltageDropResult(drop_v=5.0, drop_percent=2.0, material="Alumínio")
        # Should NOT appear in repr (not a dataclass field)
        assert "LIMIT_PERCENT" not in repr(r)


# ─── SpanResult ───────────────────────────────────────────────────────────────


class TestSpanResult:
    def test_valid_span_result(self):
        """SpanResult válido é criado com sucesso."""
        s = SpanResult(vao=100.0, angulo=15.0, flecha=1.5)
        assert s.vao == 100.0
        assert s.angulo == 15.0
        assert s.flecha == 1.5

    def test_span_zero_vao_valid(self):
        """Vão zero é válido (ponto de apoio sem vão)."""
        s = SpanResult(vao=0.0, angulo=0.0, flecha=0.0)
        assert s.vao == 0.0

    def test_span_is_immutable(self):
        """SpanResult é imutável."""
        s = SpanResult(vao=100.0, angulo=15.0, flecha=1.5)
        with pytest.raises((TypeError, AttributeError)):
            s.vao = 200.0  # type: ignore[misc]

    def test_negative_vao_raises(self):
        """Vão negativo levanta ValueError."""
        with pytest.raises(ValueError, match="Comprimento do vão"):
            SpanResult(vao=-10.0, angulo=0.0, flecha=1.0)

    def test_angulo_out_of_range_raises(self):
        """Ângulo acima de 360° levanta ValueError."""
        with pytest.raises(ValueError, match="Ângulo deve estar entre"):
            SpanResult(vao=100.0, angulo=361.0, flecha=1.0)

    def test_negative_flecha_raises(self):
        """Flecha negativa levanta ValueError."""
        with pytest.raises(ValueError, match="Flecha não pode ser negativa"):
            SpanResult(vao=100.0, angulo=0.0, flecha=-0.1)

    def test_angulo_boundary_360(self):
        """Ângulo exatamente 360° é válido."""
        s = SpanResult(vao=100.0, angulo=360.0, flecha=1.0)
        assert s.angulo == 360.0


# ─── Conductor ────────────────────────────────────────────────────────────────


class TestConductor:
    def test_valid_conductor(self):
        """Condutor válido é criado com sucesso."""
        c = Conductor(name="556MCM-CA", weight_kg_m=1.594, breaking_load_daN=13750.0)
        assert c.name == "556MCM-CA"
        assert c.section_mm2 is None  # optional

    def test_conductor_with_section(self):
        """Condutor com seção explícita."""
        c = Conductor(name="1/0AWG-CAA", weight_kg_m=0.625, breaking_load_daN=5240.0, section_mm2=53.5)
        assert c.section_mm2 == 53.5

    def test_conductor_empty_name_raises(self):
        """Nome vazio levanta ValueError."""
        with pytest.raises(ValueError, match="Nome do condutor"):
            Conductor(name="", weight_kg_m=1.0, breaking_load_daN=5000.0)

    def test_conductor_negative_weight_raises(self):
        """Peso linear negativo levanta ValueError."""
        with pytest.raises(ValueError, match="Peso linear"):
            Conductor(name="556MCM-CA", weight_kg_m=-1.0, breaking_load_daN=5000.0)

    def test_conductor_zero_breaking_load_raises(self):
        """Carga de ruptura zero levanta ValueError."""
        with pytest.raises(ValueError, match="Carga de ruptura"):
            Conductor(name="556MCM-CA", weight_kg_m=1.0, breaking_load_daN=0.0)

    def test_conductor_zero_section_raises(self):
        """Seção zero levanta ValueError."""
        with pytest.raises(ValueError, match="Seção transversal"):
            Conductor(name="556MCM-CA", weight_kg_m=1.0, breaking_load_daN=5000.0, section_mm2=0.0)

    def test_conductor_zero_weight_valid(self):
        """Peso linear zero é permitido (condutor incomum mas válido)."""
        c = Conductor(name="FioCentoTest", weight_kg_m=0.0, breaking_load_daN=100.0)
        assert c.weight_kg_m == 0.0


# ─── Pole ─────────────────────────────────────────────────────────────────────


class TestPole:
    def test_valid_pole(self):
        """Poste válido é criado com sucesso."""
        p = Pole(material="Concreto", height_m=11.0, format="Circular", nominal_load_daN=300.0)
        assert p.material == "Concreto"
        assert p.nominal_load_daN == 300.0

    def test_pole_empty_material_raises(self):
        """Material vazio levanta ValueError."""
        with pytest.raises(ValueError, match="Material do poste"):
            Pole(material="", height_m=11.0, format="Circular", nominal_load_daN=300.0)

    def test_pole_zero_height_raises(self):
        """Altura zero levanta ValueError."""
        with pytest.raises(ValueError, match="Altura do poste"):
            Pole(material="Concreto", height_m=0.0, format="Circular", nominal_load_daN=300.0)

    def test_pole_empty_format_raises(self):
        """Formato vazio levanta ValueError."""
        with pytest.raises(ValueError, match="Formato do poste"):
            Pole(material="Concreto", height_m=11.0, format="", nominal_load_daN=300.0)

    def test_pole_zero_load_raises(self):
        """Carga nominal zero levanta ValueError."""
        with pytest.raises(ValueError, match="Carga nominal"):
            Pole(material="Concreto", height_m=11.0, format="Circular", nominal_load_daN=0.0)


# ─── Concessionaire ───────────────────────────────────────────────────────────


class TestConcessionaire:
    def test_valid_concessionaire_flecha(self):
        """Concessionária com método flecha é válida."""
        c = Concessionaire(name="Light", method="flecha")
        assert c.name == "Light"
        assert c.method == "flecha"

    def test_valid_concessionaire_tabela(self):
        """Concessionária com método tabela é válida."""
        c = Concessionaire(name="Enel", method="tabela")
        assert c.method == "tabela"

    def test_concessionaire_empty_name_raises(self):
        """Nome vazio levanta ValueError."""
        with pytest.raises(ValueError, match="Nome da concessionária"):
            Concessionaire(name="", method="flecha")

    def test_concessionaire_invalid_method_raises(self):
        """Método inválido levanta ValueError com mensagem informativa."""
        with pytest.raises(ValueError, match="Método inválido"):
            Concessionaire(name="Light", method="invalido")

    def test_concessionaire_valid_methods_class_var(self):
        """VALID_METHODS é acessível como variável de classe."""
        assert "flecha" in Concessionaire.VALID_METHODS
        assert "tabela" in Concessionaire.VALID_METHODS
        assert len(Concessionaire.VALID_METHODS) == 2
