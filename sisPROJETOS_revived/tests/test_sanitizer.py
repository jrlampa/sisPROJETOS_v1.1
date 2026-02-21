"""
Testes unitários para o módulo de sanitização de dados (src/utils/sanitizer.py).

Cobre:
- sanitize_string: remoção de caracteres de controle, truncamento, strip, vazio
- sanitize_numeric: conversão, mínimo, máximo, default, falhas
- sanitize_positive: valores positivos e erros
- sanitize_power_factor: intervalo (0, 1]
- sanitize_phases: valores 1 e 3 e erros
- sanitize_filepath: extensões, nulos, vazio
- sanitize_code: alfanumérico, maiúsculas, caracteres inválidos
"""

import pytest

from src.utils.sanitizer import (
    sanitize_code,
    sanitize_filepath,
    sanitize_numeric,
    sanitize_phases,
    sanitize_positive,
    sanitize_power_factor,
    sanitize_string,
)

# ---------------------------------------------------------------------------
# sanitize_string
# ---------------------------------------------------------------------------


class TestSanitizeString:
    def test_basic_string(self):
        assert sanitize_string("hello") == "hello"

    def test_strips_whitespace_by_default(self):
        assert sanitize_string("  João  ") == "João"

    def test_no_strip_when_disabled(self):
        result = sanitize_string("  texto  ", strip=False)
        assert result == "  texto  "

    def test_removes_null_bytes(self):
        assert sanitize_string("abc\x00def") == "abcdef"

    def test_removes_control_characters(self):
        # \x01–\x08 são caracteres de controle
        assert sanitize_string("abc\x01\x07def") == "abcdef"

    def test_preserves_tab_and_newline(self):
        # \t (\x09) e \n (\x0a) devem ser preservados
        result = sanitize_string("a\tb\nc", strip=False)
        assert "\t" in result
        assert "\n" in result

    def test_truncates_to_max_length(self):
        result = sanitize_string("a" * 300, max_length=50)
        assert len(result) == 50

    def test_max_length_zero_means_no_limit(self):
        long_str = "a" * 600
        result = sanitize_string(long_str, max_length=0)
        assert len(result) == 600

    def test_converts_none_to_empty_with_allow_empty(self):
        result = sanitize_string(None, allow_empty=True)
        assert result == ""

    def test_none_raises_when_not_allow_empty(self):
        with pytest.raises(ValueError, match="não pode ser vazio"):
            sanitize_string(None)

    def test_empty_string_raises_when_not_allow_empty(self):
        with pytest.raises(ValueError, match="não pode ser vazio"):
            sanitize_string("")

    def test_empty_string_ok_with_allow_empty(self):
        result = sanitize_string("", allow_empty=True)
        assert result == ""

    def test_unicode_normalization(self):
        # Letras acentuadas devem ser preservadas via NFC
        result = sanitize_string("São Paulo")
        assert result == "São Paulo"

    def test_non_string_converted(self):
        assert sanitize_string(42) == "42"
        assert sanitize_string(3.14) == "3.14"


# ---------------------------------------------------------------------------
# sanitize_numeric
# ---------------------------------------------------------------------------


class TestSanitizeNumeric:
    def test_float_string(self):
        assert sanitize_numeric("42.5") == 42.5

    def test_integer_value(self):
        assert sanitize_numeric(10) == 10.0

    def test_min_val_accepted(self):
        assert sanitize_numeric(0.0, min_val=0.0) == 0.0

    def test_below_min_raises(self):
        with pytest.raises(ValueError, match="abaixo do mínimo"):
            sanitize_numeric(-1.0, min_val=0.0)

    def test_max_val_accepted(self):
        assert sanitize_numeric(100.0, max_val=100.0) == 100.0

    def test_above_max_raises(self):
        with pytest.raises(ValueError, match="acima do máximo"):
            sanitize_numeric(101.0, max_val=100.0)

    def test_invalid_string_uses_default(self):
        assert sanitize_numeric("abc", default=0.0) == 0.0

    def test_invalid_string_raises_when_no_default(self):
        with pytest.raises(ValueError, match="não é numérico"):
            sanitize_numeric("abc")

    def test_none_uses_default(self):
        assert sanitize_numeric(None, default=5.0) == 5.0

    def test_none_raises_when_no_default(self):
        with pytest.raises(ValueError):
            sanitize_numeric(None)

    def test_range_min_and_max(self):
        assert sanitize_numeric(50, min_val=0, max_val=100) == 50.0


# ---------------------------------------------------------------------------
# sanitize_positive
# ---------------------------------------------------------------------------


class TestSanitizePositive:
    def test_positive_float(self):
        assert sanitize_positive("10.5") == 10.5

    def test_positive_int(self):
        assert sanitize_positive(1) == 1.0

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="deve ser positivo"):
            sanitize_positive(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="deve ser positivo"):
            sanitize_positive(-5.0)

    def test_invalid_uses_default_but_still_validates_sign(self):
        # Default 0 is not positive — should raise
        with pytest.raises(ValueError, match="deve ser positivo"):
            sanitize_positive("abc", default=0.0)

    def test_valid_default(self):
        assert sanitize_positive("abc", default=1.0) == 1.0


# ---------------------------------------------------------------------------
# sanitize_power_factor
# ---------------------------------------------------------------------------


class TestSanitizePowerFactor:
    def test_typical_value(self):
        assert sanitize_power_factor(0.92) == 0.92

    def test_unity_power_factor(self):
        assert sanitize_power_factor(1.0) == 1.0

    def test_very_small_positive(self):
        assert sanitize_power_factor(0.01) == 0.01

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="cos φ"):
            sanitize_power_factor(0.0)

    def test_above_one_raises(self):
        with pytest.raises(ValueError, match="cos φ"):
            sanitize_power_factor(1.01)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="cos φ"):
            sanitize_power_factor(-0.5)

    def test_string_value(self):
        assert sanitize_power_factor("0.85") == 0.85


# ---------------------------------------------------------------------------
# sanitize_phases
# ---------------------------------------------------------------------------


class TestSanitizePhases:
    def test_monophasic(self):
        assert sanitize_phases(1) == 1

    def test_triphasic(self):
        assert sanitize_phases(3) == 3

    def test_string_int(self):
        assert sanitize_phases("3") == 3

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError, match="deve ser 1 ou 3"):
            sanitize_phases(2)

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="deve ser 1 ou 3"):
            sanitize_phases(0)

    def test_non_integer_string_raises(self):
        with pytest.raises(ValueError, match="inválido"):
            sanitize_phases("monofásico")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            sanitize_phases(None)


# ---------------------------------------------------------------------------
# sanitize_filepath
# ---------------------------------------------------------------------------


class TestSanitizeFilepath:
    def test_valid_path(self):
        assert sanitize_filepath("output.dxf") == "output.dxf"

    def test_strips_whitespace(self):
        assert sanitize_filepath("  output.xlsx  ") == "output.xlsx"

    def test_none_raises(self):
        with pytest.raises(ValueError, match="string não nula"):
            sanitize_filepath(None)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="não pode ser vazio"):
            sanitize_filepath("")

    def test_null_byte_raises(self):
        with pytest.raises(ValueError, match="bytes nulos"):
            sanitize_filepath("output\x00.dxf")

    def test_allowed_extension_accepted(self):
        result = sanitize_filepath("output.dxf", allowed_extensions=[".dxf", ".dwg"])
        assert result == "output.dxf"

    def test_disallowed_extension_raises(self):
        with pytest.raises(ValueError, match="Extensão"):
            sanitize_filepath("output.exe", allowed_extensions=[".dxf", ".xlsx"])

    def test_case_insensitive_extension(self):
        result = sanitize_filepath("output.DXF", allowed_extensions=[".dxf"])
        assert result == "output.DXF"

    def test_no_extension_restriction(self):
        result = sanitize_filepath("output.anything")
        assert result == "output.anything"

    def test_path_with_directory(self):
        result = sanitize_filepath("/tmp/output.dxf", allowed_extensions=[".dxf"])
        assert result == "/tmp/output.dxf"

    def test_non_string_raises(self):
        with pytest.raises(ValueError, match="string não nula"):
            sanitize_filepath(123)


# ---------------------------------------------------------------------------
# sanitize_code
# ---------------------------------------------------------------------------


class TestSanitizeCode:
    def test_alphanumeric_code(self):
        assert sanitize_code("ZX323948246") == "ZX323948246"

    def test_hyphen_and_underscore_allowed(self):
        assert sanitize_code("ZX-323948246_A") == "ZX-323948246_A"

    def test_converts_to_uppercase(self):
        assert sanitize_code("zx123") == "ZX123"

    def test_removes_special_chars(self):
        # Espaços e outros caracteres são removidos
        result = sanitize_code("AB 123")
        assert result == "AB123"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            sanitize_code("")

    def test_only_invalid_chars_raises(self):
        with pytest.raises(ValueError, match="caracteres válidos"):
            sanitize_code("@#$%")

    def test_truncated_to_max_length(self):
        result = sanitize_code("A" * 40, max_length=30)
        assert len(result) == 30

    def test_none_raises(self):
        with pytest.raises(ValueError):
            sanitize_code(None)
