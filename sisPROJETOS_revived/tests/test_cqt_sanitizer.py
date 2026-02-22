"""
Testes de sanitização de entradas para o módulo CQT.

Cobre validação de trafo_kva e social_class em CQTLogic.calculate().
"""

import pytest

from src.modules.cqt.logic import CQTLogic


class TestCQTSanitizer:
    """Testes para validação de entradas no método calculate."""

    @pytest.fixture
    def cqt(self):
        return CQTLogic()

    @pytest.fixture
    def valid_segments(self):
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
                "metros": 50,
                "cabo": "3x35+54.6mm² Al",
                "mono": 5,
                "bi": 0,
                "tri": 0,
                "tri_esp": 0,
                "carga_esp": 0,
            },
        ]

    def test_invalid_trafo_kva_zero_returns_error(self, cqt, valid_segments):
        """Sanitizer: trafo_kva=0 deve retornar erro."""
        result = cqt.calculate(valid_segments, trafo_kva=0, social_class="B")
        assert result["success"] is False
        assert "error" in result

    def test_invalid_trafo_kva_negative_returns_error(self, cqt, valid_segments):
        """Sanitizer: trafo_kva negativo deve retornar erro."""
        result = cqt.calculate(valid_segments, trafo_kva=-100, social_class="B")
        assert result["success"] is False

    def test_invalid_social_class_returns_error(self, cqt, valid_segments):
        """Sanitizer: classe social inválida deve retornar erro."""
        result = cqt.calculate(valid_segments, trafo_kva=112.5, social_class="X")
        assert result["success"] is False
        assert "error" in result

    def test_valid_social_class_lowercase_accepted(self, cqt, valid_segments):
        """Sanitizer: classe social em minúscula deve ser normalizada."""
        result = cqt.calculate(valid_segments, trafo_kva=112.5, social_class="b")
        assert result["success"] is True
