"""
Testes para padrões regulatórios ANEEL/PRODIST e mecanismo de toast (domain/standards.py).

Verifica:
    - VoltageStandard: criação, validação, imutabilidade, check()
    - Padrões pré-definidos: NBR_5410, PRODIST_MODULE8_BT, PRODIST_MODULE8_MT,
      LIGHT_BT, ENEL_BT
    - ALL_STANDARDS e get_standard_by_name()
    - Integração com VoltageDropResult.is_within_standard()
    - Integração com VoltageDropDomainService.calculate(standard=...)
    - Toast: overrides_abnt=True requer override_toast_pt_br não-vazio
    - Hierarquia normativa: concessionaire > PRODIST > ABNT
"""

import pytest

from domain.services import VoltageDropDomainService
from domain.standards import (
    ALL_STANDARDS,
    ENEL_BT,
    LIGHT_BT,
    NBR_5410,
    PRODIST_MODULE8_BT,
    PRODIST_MODULE8_MT,
    VoltageStandard,
    get_standard_by_name,
)
from domain.value_objects import VoltageDropResult

# ─── VoltageStandard: Criação e validação ─────────────────────────────────────


class TestVoltageStandardCreation:
    def test_valid_abnt_standard(self):
        """VoltageStandard ABNT é criado com sucesso."""
        s = VoltageStandard(name="NBR 5410", source="ABNT", max_drop_percent=5.0, overrides_abnt=False)
        assert s.name == "NBR 5410"
        assert s.source == "ABNT"
        assert s.max_drop_percent == 5.0
        assert s.overrides_abnt is False
        assert s.override_toast_pt_br == ""

    def test_valid_prodist_standard(self):
        """VoltageStandard ANEEL/PRODIST é criado com sucesso."""
        s = VoltageStandard(
            name="PRODIST BT",
            source="ANEEL/PRODIST",
            max_drop_percent=8.0,
            overrides_abnt=True,
            override_toast_pt_br="⚠️ PRODIST aplicado.",
        )
        assert s.max_drop_percent == 8.0
        assert s.overrides_abnt is True
        assert "PRODIST" in s.override_toast_pt_br

    def test_valid_concessionaire_standard(self):
        """VoltageStandard de concessionária é criado com sucesso."""
        s = VoltageStandard(
            name="Light BT",
            source="CONCESSIONAIRE",
            max_drop_percent=8.0,
            overrides_abnt=True,
            override_toast_pt_br="⚠️ Light aplica PRODIST.",
        )
        assert s.source == "CONCESSIONAIRE"
        assert s.overrides_abnt is True

    def test_standard_is_immutable(self):
        """VoltageStandard é imutável (frozen=True)."""
        s = VoltageStandard(name="NBR 5410", source="ABNT", max_drop_percent=5.0, overrides_abnt=False)
        with pytest.raises((TypeError, AttributeError)):
            s.max_drop_percent = 10.0  # type: ignore[misc]

    def test_invalid_name_empty(self):
        """Nome vazio levanta ValueError."""
        with pytest.raises(ValueError, match="Nome do padrão é obrigatório"):
            VoltageStandard(name="", source="ABNT", max_drop_percent=5.0, overrides_abnt=False)

    def test_invalid_source(self):
        """Fonte inválida levanta ValueError."""
        with pytest.raises(ValueError, match="Fonte inválida"):
            VoltageStandard(name="X", source="DESCONHECIDA", max_drop_percent=5.0, overrides_abnt=False)

    def test_invalid_max_drop_zero(self):
        """max_drop_percent=0 levanta ValueError."""
        with pytest.raises(ValueError, match="Limite de queda deve ser positivo"):
            VoltageStandard(name="X", source="ABNT", max_drop_percent=0.0, overrides_abnt=False)

    def test_invalid_max_drop_negative(self):
        """max_drop_percent negativo levanta ValueError."""
        with pytest.raises(ValueError, match="Limite de queda deve ser positivo"):
            VoltageStandard(name="X", source="ABNT", max_drop_percent=-1.0, overrides_abnt=False)

    def test_overrides_abnt_without_toast_raises(self):
        """overrides_abnt=True sem toast levanta ValueError."""
        with pytest.raises(ValueError, match="override_toast_pt_br"):
            VoltageStandard(
                name="Y",
                source="ANEEL/PRODIST",
                max_drop_percent=8.0,
                overrides_abnt=True,
                override_toast_pt_br="",
            )

    def test_overrides_abnt_false_without_toast_ok(self):
        """overrides_abnt=False sem toast é válido (campo é opcional)."""
        s = VoltageStandard(name="NBR", source="ABNT", max_drop_percent=5.0, overrides_abnt=False)
        assert s.override_toast_pt_br == ""


# ─── VoltageStandard.check() ──────────────────────────────────────────────────


class TestVoltageStandardCheck:
    def test_check_within_limit(self):
        """check() retorna True quando queda ≤ max_drop_percent."""
        s = VoltageStandard(name="NBR", source="ABNT", max_drop_percent=5.0, overrides_abnt=False)
        assert s.check(4.9) is True
        assert s.check(5.0) is True  # boundary

    def test_check_over_limit(self):
        """check() retorna False quando queda > max_drop_percent."""
        s = VoltageStandard(name="NBR", source="ABNT", max_drop_percent=5.0, overrides_abnt=False)
        assert s.check(5.1) is False
        assert s.check(10.0) is False

    def test_check_zero_drop(self):
        """check() com queda zero é sempre True."""
        s = VoltageStandard(name="NBR", source="ABNT", max_drop_percent=5.0, overrides_abnt=False)
        assert s.check(0.0) is True

    def test_check_prodist_bt_limit(self):
        """PRODIST BT aceita até 8%."""
        s = VoltageStandard(
            name="BT",
            source="ANEEL/PRODIST",
            max_drop_percent=8.0,
            overrides_abnt=True,
            override_toast_pt_br="⚠️ PRODIST.",
        )
        assert s.check(7.99) is True
        assert s.check(8.0) is True
        assert s.check(8.01) is False


# ─── Padrões pré-definidos ────────────────────────────────────────────────────


class TestPredefinedStandards:
    def test_nbr_5410_values(self):
        """NBR_5410 tem limite 5%, source ABNT, não sobrepõe ABNT."""
        assert NBR_5410.name == "NBR 5410"
        assert NBR_5410.source == "ABNT"
        assert NBR_5410.max_drop_percent == 5.0
        assert NBR_5410.overrides_abnt is False
        assert NBR_5410.override_toast_pt_br == ""

    def test_prodist_module8_bt_values(self):
        """PRODIST_MODULE8_BT tem limite 8%, source ANEEL/PRODIST, sobrepõe ABNT."""
        assert PRODIST_MODULE8_BT.source == "ANEEL/PRODIST"
        assert PRODIST_MODULE8_BT.max_drop_percent == 8.0
        assert PRODIST_MODULE8_BT.overrides_abnt is True
        assert "8%" in PRODIST_MODULE8_BT.override_toast_pt_br
        assert "PRODIST" in PRODIST_MODULE8_BT.override_toast_pt_br

    def test_prodist_module8_mt_values(self):
        """PRODIST_MODULE8_MT tem limite 7%, source ANEEL/PRODIST, sobrepõe ABNT."""
        assert PRODIST_MODULE8_MT.source == "ANEEL/PRODIST"
        assert PRODIST_MODULE8_MT.max_drop_percent == 7.0
        assert PRODIST_MODULE8_MT.overrides_abnt is True
        assert "7%" in PRODIST_MODULE8_MT.override_toast_pt_br

    def test_light_bt_values(self):
        """LIGHT_BT tem limite 8%, source CONCESSIONAIRE, sobrepõe ABNT com toast Light."""
        assert LIGHT_BT.source == "CONCESSIONAIRE"
        assert LIGHT_BT.max_drop_percent == 8.0
        assert LIGHT_BT.overrides_abnt is True
        assert "Light" in LIGHT_BT.override_toast_pt_br

    def test_enel_bt_values(self):
        """ENEL_BT tem limite 8%, source CONCESSIONAIRE, sobrepõe ABNT com toast Enel."""
        assert ENEL_BT.source == "CONCESSIONAIRE"
        assert ENEL_BT.max_drop_percent == 8.0
        assert ENEL_BT.overrides_abnt is True
        assert "Enel" in ENEL_BT.override_toast_pt_br

    def test_all_standards_contains_five(self):
        """ALL_STANDARDS contém os 5 padrões pré-definidos."""
        assert len(ALL_STANDARDS) == 5
        names = {s.name for s in ALL_STANDARDS}
        assert "NBR 5410" in names
        assert "PRODIST Módulo 8 — BT" in names
        assert "PRODIST Módulo 8 — MT" in names

    def test_all_standards_is_frozenset(self):
        """ALL_STANDARDS é um frozenset (imutável)."""
        assert isinstance(ALL_STANDARDS, frozenset)
        with pytest.raises((TypeError, AttributeError)):
            ALL_STANDARDS.add(NBR_5410)  # type: ignore[attr-defined]

    def test_toast_messages_in_portuguese(self):
        """Mensagens de toast estão em português e mencionam ABNT."""
        for std in ALL_STANDARDS:
            if std.overrides_abnt:
                assert "ABNT" in std.override_toast_pt_br, f"{std.name}: toast deveria mencionar ABNT"

    def test_concessionaire_standards_mention_prodist(self):
        """Padrões de concessionária mencionam PRODIST no toast."""
        assert "PRODIST" in LIGHT_BT.override_toast_pt_br
        assert "PRODIST" in ENEL_BT.override_toast_pt_br


# ─── get_standard_by_name() ───────────────────────────────────────────────────


class TestGetStandardByName:
    def test_get_nbr_5410(self):
        """Busca NBR 5410 por nome retorna o padrão correto."""
        result = get_standard_by_name("NBR 5410")
        assert result is NBR_5410

    def test_get_prodist_bt(self):
        """Busca PRODIST BT por nome retorna o padrão correto."""
        result = get_standard_by_name("PRODIST Módulo 8 — BT")
        assert result is PRODIST_MODULE8_BT

    def test_get_light_bt(self):
        """Busca Light BT por nome retorna o padrão correto."""
        result = get_standard_by_name("Light — BT (PRODIST Módulo 8)")
        assert result is LIGHT_BT

    def test_get_enel_bt(self):
        """Busca Enel BT por nome retorna o padrão correto."""
        result = get_standard_by_name("Enel — BT (PRODIST Módulo 8)")
        assert result is ENEL_BT

    def test_get_unknown_returns_none(self):
        """Nome desconhecido retorna None."""
        assert get_standard_by_name("INEXISTENTE") is None

    def test_get_case_sensitive(self):
        """Busca é case-sensitive."""
        assert get_standard_by_name("nbr 5410") is None


# ─── Integração: VoltageDropResult.is_within_standard() ──────────────────────


class TestVoltageDropResultIsWithinStandard:
    def test_within_nbr_5410(self):
        """Queda de 4.9% está dentro da NBR 5410."""
        r = VoltageDropResult(drop_v=10.0, drop_percent=4.9, material="Alumínio")
        assert r.is_within_standard(NBR_5410) is True

    def test_exceeds_nbr_but_within_prodist_bt(self):
        """Queda de 6.5% excede NBR 5410 mas está dentro do PRODIST BT."""
        r = VoltageDropResult(drop_v=14.0, drop_percent=6.5, material="Alumínio")
        assert r.is_within_standard(NBR_5410) is False
        assert r.is_within_standard(PRODIST_MODULE8_BT) is True

    def test_exceeds_nbr_but_within_light(self):
        """Queda de 7.5% excede NBR mas está dentro da norma Light (8%)."""
        r = VoltageDropResult(drop_v=16.0, drop_percent=7.5, material="Alumínio")
        assert r.is_within_limit is False
        assert r.is_within_standard(LIGHT_BT) is True
        assert r.is_within_standard(ENEL_BT) is True

    def test_exceeds_prodist_bt(self):
        """Queda de 8.1% excede todos os padrões BT."""
        r = VoltageDropResult(drop_v=18.0, drop_percent=8.1, material="Alumínio")
        assert r.is_within_limit is False
        assert r.is_within_standard(NBR_5410) is False
        assert r.is_within_standard(PRODIST_MODULE8_BT) is False
        assert r.is_within_standard(LIGHT_BT) is False

    def test_exceeds_nbr_but_within_prodist_mt(self):
        """Queda de 6.9% excede NBR mas está dentro do PRODIST MT (7%)."""
        r = VoltageDropResult(drop_v=14.0, drop_percent=6.9, material="Cobre")
        assert r.is_within_standard(NBR_5410) is False
        assert r.is_within_standard(PRODIST_MODULE8_MT) is True

    def test_is_within_limit_is_unchanged(self):
        """is_within_limit (NBR 5410) continua funcionando após adição do método novo."""
        r = VoltageDropResult(drop_v=10.0, drop_percent=4.0, material="Cobre")
        assert r.is_within_limit is True
        r2 = VoltageDropResult(drop_v=12.0, drop_percent=5.5, material="Cobre")
        assert r2.is_within_limit is False


# ─── Integração: VoltageDropDomainService.calculate(standard=...) ─────────────


class TestVoltageDropServiceWithStandard:
    def setup_method(self):
        self.svc = VoltageDropDomainService()

    def test_service_without_standard_uses_default(self):
        """Serviço sem standard retorna resultado verificável com is_within_limit."""
        result = self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3)
        assert result.drop_percent >= 0
        # is_within_limit usa NBR 5410 (5%)
        assert isinstance(result.is_within_limit, bool)

    def test_service_with_nbr_5410(self):
        """Serviço com NBR_5410 produz o mesmo resultado (padrão)."""
        r1 = self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3)
        r2 = self.svc.calculate("Alumínio", 0.0282, 100.0, 10.0, 35.0, 380.0, 3, standard=NBR_5410)
        assert r1.drop_percent == r2.drop_percent
        assert r2.is_within_standard(NBR_5410) == r2.is_within_limit

    def test_service_with_prodist_bt_more_permissive(self):
        """PRODIST BT é mais permissivo que NBR 5410 — aceita queda > 5%."""
        # Longa linha + seção pequena para forçar queda > 5%
        result = self.svc.calculate("Alumínio", 0.0282, 500.0, 50.0, 16.0, 220.0, 1, standard=PRODIST_MODULE8_BT)
        # Verificar que é conforme PRODIST mas não NBR 5410
        if result.drop_percent > 5.0:
            assert result.is_within_limit is False
            assert result.is_within_standard(PRODIST_MODULE8_BT) is (result.drop_percent <= 8.0)

    def test_service_with_light_bt_toast_accessible(self):
        """Toast da Light está acessível através do standard passado."""
        result = self.svc.calculate("Alumínio", 0.0282, 200.0, 20.0, 35.0, 220.0, 1, standard=LIGHT_BT)
        assert LIGHT_BT.overrides_abnt is True
        assert "Light" in LIGHT_BT.override_toast_pt_br
        assert result.drop_percent >= 0

    def test_service_with_enel_bt_toast_accessible(self):
        """Toast da Enel está acessível através do standard passado."""
        result = self.svc.calculate("Alumínio", 0.0282, 200.0, 20.0, 35.0, 220.0, 1, standard=ENEL_BT)
        assert ENEL_BT.overrides_abnt is True
        assert "Enel" in ENEL_BT.override_toast_pt_br
        assert result.drop_percent >= 0

    def test_service_standard_does_not_change_formula(self):
        """Passar standard não altera o cálculo numérico."""
        r_sem = self.svc.calculate("Cobre", 0.0175, 100.0, 15.0, 25.0, 380.0, 3)
        r_com = self.svc.calculate("Cobre", 0.0175, 100.0, 15.0, 25.0, 380.0, 3, standard=PRODIST_MODULE8_BT)
        assert r_sem.drop_v == r_com.drop_v
        assert r_sem.drop_percent == r_com.drop_percent

    def test_concessionaire_standard_overrides_abnt_flag(self):
        """Padrões de concessionária sempre têm overrides_abnt=True."""
        assert LIGHT_BT.overrides_abnt is True
        assert ENEL_BT.overrides_abnt is True
        # Padrão ABNT nunca sobrepõe a si mesmo
        assert NBR_5410.overrides_abnt is False


# ─── Hierarquia normativa ─────────────────────────────────────────────────────


class TestNormativeHierarchy:
    """Valida a hierarquia CONCESSIONAIRE > ANEEL/PRODIST > ABNT."""

    def test_nbr_is_most_restrictive(self):
        """NBR 5410 tem o menor limite (mais restritivo)."""
        assert NBR_5410.max_drop_percent < PRODIST_MODULE8_MT.max_drop_percent
        assert PRODIST_MODULE8_MT.max_drop_percent < PRODIST_MODULE8_BT.max_drop_percent

    def test_prodist_bt_equals_concessionaire_bt(self):
        """Concessionárias BT adotam o mesmo limite do PRODIST Módulo 8 BT."""
        assert LIGHT_BT.max_drop_percent == PRODIST_MODULE8_BT.max_drop_percent
        assert ENEL_BT.max_drop_percent == PRODIST_MODULE8_BT.max_drop_percent

    def test_only_abnt_does_not_override(self):
        """Apenas o padrão ABNT não sobrepõe a si mesmo."""
        non_overriding = [s for s in ALL_STANDARDS if not s.overrides_abnt]
        assert len(non_overriding) == 1
        assert non_overriding[0].source == "ABNT"

    def test_all_overriding_have_toast(self):
        """Todo padrão com overrides_abnt=True tem toast pt-BR não-vazio."""
        for std in ALL_STANDARDS:
            if std.overrides_abnt:
                assert std.override_toast_pt_br, f"{std.name} deveria ter toast pt-BR"
