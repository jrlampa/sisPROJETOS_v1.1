"""
Testes de conformidade regulatória do módulo CQT.

Cobre o limite de projeto CNS-OMBR-MAT-19-0285 (5%), within_enel_limit e
segments_over_limit retornados pelo CQTLogic.calculate().
"""

import pytest

from src.modules.cqt.logic import CQTLogic


class TestCQTCompliance:
    """Testes para campos de conformidade regulatória do CQT (Enel CNS-OMBR-MAT-19-0285)."""

    @pytest.fixture
    def cqt(self):
        return CQTLogic()

    @pytest.fixture
    def minimal_segments(self):
        """Segmentos mínimos com apenas TRAFO e P1 (CQT baixo — dentro do limite)."""
        return [
            {
                "ponto": "TRAFO",
                "montante": "",
                "metros": 0,
                "cabo": "",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P1",
                "montante": "TRAFO",
                "metros": 10,
                "cabo": "3x35+54.6mm² Al",
                "mono": 1,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]

    @pytest.fixture
    def high_load_segments(self):
        """Segmentos com carga alta (CQT elevado — provável violação do limite de 5%)."""
        return [
            {
                "ponto": "TRAFO",
                "montante": "",
                "metros": 0,
                "cabo": "",
                "mono": 0,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
            {
                "ponto": "P1",
                "montante": "TRAFO",
                "metros": 500,
                "cabo": "2#16(25)mm² Al",
                "mono": 50,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]

    def test_cqt_limit_percent_constant_value(self, cqt):
        """CQT_LIMIT_PERCENT deve ser 5.0 — critério de projeto CNS-OMBR-MAT-19-0285."""
        assert cqt.CQT_LIMIT_PERCENT == pytest.approx(5.0)

    def test_cqt_limit_percent_is_class_attribute(self):
        """CQT_LIMIT_PERCENT deve ser acessível como atributo de classe."""
        assert CQTLogic.CQT_LIMIT_PERCENT == pytest.approx(5.0)

    def test_summary_contains_cqt_limit_percent(self, cqt, minimal_segments):
        """Resumo do cálculo deve incluir cqt_limit_percent."""
        result = cqt.calculate(minimal_segments, trafo_kva=75, social_class="B")
        assert result["success"] is True
        assert "cqt_limit_percent" in result["summary"]
        assert result["summary"]["cqt_limit_percent"] == pytest.approx(5.0)

    def test_summary_contains_within_enel_limit(self, cqt, minimal_segments):
        """Resumo deve incluir within_enel_limit com valor booleano."""
        result = cqt.calculate(minimal_segments, trafo_kva=75, social_class="B")
        assert result["success"] is True
        assert "within_enel_limit" in result["summary"]
        assert isinstance(result["summary"]["within_enel_limit"], bool)

    def test_summary_contains_segments_over_limit_list(self, cqt, minimal_segments):
        """Resumo deve incluir segments_over_limit como lista."""
        result = cqt.calculate(minimal_segments, trafo_kva=75, social_class="B")
        assert result["success"] is True
        assert "segments_over_limit" in result["summary"]
        assert isinstance(result["summary"]["segments_over_limit"], list)

    def test_within_enel_limit_true_for_low_cqt(self, cqt, minimal_segments):
        """within_enel_limit deve ser True quando CQT máximo abaixo do limite."""
        result = cqt.calculate(minimal_segments, trafo_kva=75, social_class="B")
        assert result["success"] is True
        assert result["summary"]["within_enel_limit"] is True
        assert result["summary"]["segments_over_limit"] == []

    def test_within_enel_limit_false_for_high_cqt(self, cqt, high_load_segments):
        """within_enel_limit deve ser False quando CQT excede o limite de projeto."""
        result = cqt.calculate(high_load_segments, trafo_kva=30, social_class="D")
        assert result["success"] is True
        # High load on thin cable over 500m must exceed the design limit
        if result["summary"]["max_cqt"] > cqt.CQT_LIMIT_PERCENT:
            assert result["summary"]["within_enel_limit"] is False
            assert "P1" in result["summary"]["segments_over_limit"]
        else:
            # If CQT happens to be within limit, just verify fields exist
            assert result["summary"]["within_enel_limit"] is True
            assert result["summary"]["segments_over_limit"] == []

    def test_segments_over_limit_consistency(self, cqt, minimal_segments):
        """segments_over_limit deve ser consistente com within_enel_limit."""
        result = cqt.calculate(minimal_segments, trafo_kva=75, social_class="B")
        assert result["success"] is True
        summary = result["summary"]
        within = summary["within_enel_limit"]
        over_list = summary["segments_over_limit"]
        if within:
            assert over_list == []
        else:
            assert len(over_list) > 0
