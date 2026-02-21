"""
Testes unitários para src/__version__.py, src/styles.py e src/utils/__init__.py.

Cobre:
- Atributos de versão do pacote
- Constantes e métodos do DesignSystem
- Função resource_path segura (src/utils/__init__.py)
"""

import re
import os
import sys
import pytest


# ---------------------------------------------------------------------------
# Testes de src/__version__.py
# ---------------------------------------------------------------------------

class TestVersion:
    def test_version_exists(self):
        from src.__version__ import __version__
        assert __version__ is not None

    def test_version_is_string(self):
        from src.__version__ import __version__
        assert isinstance(__version__, str)

    def test_version_semver_format(self):
        from src.__version__ import __version__
        assert re.match(r"^\d+\.\d+\.\d+", __version__), f"Versão '{__version__}' não está no formato semver"

    def test_build_exists(self):
        from src.__version__ import __build__
        assert isinstance(__build__, str)
        assert len(__build__) > 0

    def test_author_exists(self):
        from src.__version__ import __author__
        assert isinstance(__author__, str)

    def test_license_exists(self):
        from src.__version__ import __license__
        assert isinstance(__license__, str)

    def test_copyright_exists(self):
        from src.__version__ import __copyright__
        assert isinstance(__copyright__, str)


# ---------------------------------------------------------------------------
# Testes de src/styles.py — DesignSystem
# ---------------------------------------------------------------------------

class TestDesignSystem:
    def test_design_system_importable(self):
        from src.styles import DesignSystem
        assert DesignSystem is not None

    def test_colors_are_hex_strings(self):
        from src.styles import DesignSystem
        color_attrs = [
            "BG_WINDOW", "FRAME_BG", "FRAME_BORDER", "FRAME_TRANSLUCENT",
            "ACCENT_PRIMARY", "ACCENT_SECONDARY", "ACCENT_SUCCESS",
            "ACCENT_ERROR", "ACCENT_WARNING", "TEXT_MAIN", "TEXT_DIM", "TEXT_WHITE",
        ]
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for attr in color_attrs:
            value = getattr(DesignSystem, attr)
            assert isinstance(value, str), f"{attr} deve ser string"
            assert hex_pattern.match(value), f"{attr}='{value}' não é uma cor hex válida"

    def test_geometry_attributes_are_integers(self):
        from src.styles import DesignSystem
        assert isinstance(DesignSystem.RADIUS_LG, int)
        assert isinstance(DesignSystem.RADIUS_MD, int)
        assert isinstance(DesignSystem.BORDER_WIDTH, int)
        assert DesignSystem.RADIUS_LG > DesignSystem.RADIUS_MD

    def test_font_attributes_are_tuples(self):
        from src.styles import DesignSystem
        for attr in ["FONT_HEAD", "FONT_SUBHEAD", "FONT_BODY", "FONT_BUTTON"]:
            value = getattr(DesignSystem, attr)
            assert isinstance(value, tuple), f"{attr} deve ser uma tupla"
            assert len(value) >= 2

    def test_accent_colors_are_distinct(self):
        from src.styles import DesignSystem
        colors = {
            DesignSystem.ACCENT_PRIMARY,
            DesignSystem.ACCENT_SUCCESS,
            DesignSystem.ACCENT_ERROR,
            DesignSystem.ACCENT_WARNING,
        }
        assert len(colors) == 4, "As cores de acento devem ser distintas"


# ---------------------------------------------------------------------------
# Testes de src/utils/__init__.py — resource_path (caminho válido)
# ---------------------------------------------------------------------------

class TestResourcePath:
    def test_resource_path_returns_string(self):
        from src.utils import resource_path
        result = resource_path("README.md")
        assert isinstance(result, str)

    def test_resource_path_is_absolute(self):
        from src.utils import resource_path
        result = resource_path("README.md")
        assert os.path.isabs(result)

    def test_resource_path_joins_correctly(self):
        from src.utils import resource_path
        result = resource_path("src/resources/sisprojetos.db")
        assert result.endswith("sisprojetos.db")

    def test_resource_path_non_existent_ok(self):
        """resource_path apenas resolve o caminho, não valida existência."""
        from src.utils import resource_path
        result = resource_path("nonexistent_file.xyz")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Testes dos métodos de estilo do DesignSystem
# ---------------------------------------------------------------------------

class TestDesignSystemMethods:
    def test_get_frame_style_returns_dict(self):
        from src.styles import DesignSystem
        style = DesignSystem.get_frame_style()
        assert isinstance(style, dict)
        assert "fg_color" in style
        assert "corner_radius" in style

    def test_get_button_style_primary(self):
        from src.styles import DesignSystem
        style = DesignSystem.get_button_style("primary")
        assert isinstance(style, dict)
        assert style["fg_color"] == DesignSystem.ACCENT_PRIMARY

    def test_get_button_style_secondary(self):
        from src.styles import DesignSystem
        style = DesignSystem.get_button_style("secondary")
        assert style["fg_color"] == DesignSystem.ACCENT_SECONDARY

    def test_get_button_style_default(self):
        from src.styles import DesignSystem
        style = DesignSystem.get_button_style()
        assert style["fg_color"] == DesignSystem.ACCENT_PRIMARY

    def test_get_entry_style_returns_dict(self):
        from src.styles import DesignSystem
        style = DesignSystem.get_entry_style()
        assert isinstance(style, dict)
        assert "corner_radius" in style


# ---------------------------------------------------------------------------
# Testes de src/utils/__init__.py — resource_path seguro
# ---------------------------------------------------------------------------

class TestSecureResourcePath:
    def test_path_traversal_with_dotdot_raises(self):
        from src.utils import resource_path
        with pytest.raises(ValueError, match="path traversal"):
            resource_path("../secret_file")

    def test_absolute_path_raises(self):
        from src.utils import resource_path
        with pytest.raises(ValueError, match="path traversal"):
            resource_path("/etc/passwd")

    def test_valid_path_accepted(self):
        from src.utils import resource_path
        result = resource_path("src/resources/sisprojetos.db")
        assert isinstance(result, str)
        assert "sisprojetos.db" in result
