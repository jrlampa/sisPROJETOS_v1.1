"""
Testes unitários para src/utils/resource_manager.py.

Cobre:
- Inicialização em modo desenvolvimento
- Inicialização em modo PyInstaller (frozen)
- get_template()
- template_exists()
- get_all_templates()
- Singleton get_resource_manager()
"""

import os
import sys
import types
from unittest.mock import patch

import pytest


class TestResourceManagerDev:
    """Testes em modo desenvolvimento (não-frozen)."""

    def test_initialization_dev_mode(self):
        """Testa que ResourceManager inicializa em modo dev sem erros."""
        from src.utils.resource_manager import ResourceManager

        rm = ResourceManager()
        assert rm.base_path is not None
        assert rm.templates_dir is not None

    def test_templates_dir_is_absolute(self):
        """Testa que templates_dir é um caminho absoluto."""
        from src.utils.resource_manager import ResourceManager

        rm = ResourceManager()
        assert os.path.isabs(rm.templates_dir)

    def test_get_template_returns_path(self):
        """Testa que get_template retorna um caminho."""
        from src.utils.resource_manager import ResourceManager

        rm = ResourceManager()
        path = rm.get_template("prancha.dwg")
        assert isinstance(path, str)
        assert "prancha.dwg" in path

    def test_get_template_constructs_correct_path(self):
        """Testa que get_template constrói o caminho correto."""
        from src.utils.resource_manager import ResourceManager

        rm = ResourceManager()
        path = rm.get_template("cqt.xlsx")
        assert path == os.path.join(rm.templates_dir, "cqt.xlsx")

    def test_template_exists_real_files(self):
        """Testa template_exists com arquivos reais do projeto."""
        from src.utils.resource_manager import ResourceManager

        rm = ResourceManager()
        # If templates dir exists, prancha.dwg should be there
        if os.path.exists(rm.templates_dir):
            assert rm.template_exists("prancha.dwg")

    def test_template_exists_nonexistent(self):
        """Testa template_exists com arquivo inexistente."""
        from src.utils.resource_manager import ResourceManager

        rm = ResourceManager()
        assert not rm.template_exists("arquivo_que_nao_existe_xyz.pdf")

    def test_get_all_templates_returns_list(self):
        """Testa que get_all_templates retorna uma lista."""
        from src.utils.resource_manager import ResourceManager

        rm = ResourceManager()
        templates = rm.get_all_templates()
        assert isinstance(templates, list)

    def test_get_all_templates_nonexistent_dir(self, tmp_path):
        """Testa get_all_templates quando diretório não existe."""
        from src.utils.resource_manager import ResourceManager

        rm = ResourceManager()
        rm.templates_dir = str(tmp_path / "nonexistent_templates_dir")
        templates = rm.get_all_templates()
        assert templates == []

    def test_get_all_templates_with_files(self, tmp_path):
        """Testa get_all_templates com diretório contendo arquivos."""
        from src.utils.resource_manager import ResourceManager

        # Create temp templates dir with sample files
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.dwg").write_text("DWG content")
        (templates_dir / "test.xlsx").write_text("XLSX content")

        rm = ResourceManager()
        rm.templates_dir = str(templates_dir)
        templates = rm.get_all_templates()

        assert len(templates) == 2
        assert "test.dwg" in templates
        assert "test.xlsx" in templates


class TestResourceManagerFrozen:
    """Testes em modo PyInstaller (frozen = True)."""

    def test_initialization_frozen_mode(self, tmp_path):
        """Testa inicialização quando rodando como executável PyInstaller."""
        fake_meipass = str(tmp_path / "_MEIPASS")
        os.makedirs(fake_meipass, exist_ok=True)

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", fake_meipass, create=True):
                import importlib

                from src.utils import resource_manager as rm_module

                # Re-init a fresh instance to trigger frozen path
                from src.utils.resource_manager import ResourceManager

                rm = ResourceManager()
                # In frozen mode, base_path should be _MEIPASS
                assert rm.base_path == fake_meipass
                assert os.path.join(fake_meipass, "resources", "templates") == rm.templates_dir


class TestGetResourceManagerSingleton:
    """Testes do singleton get_resource_manager()."""

    def test_get_resource_manager_returns_instance(self):
        """Testa que get_resource_manager retorna uma instância."""
        from src.utils.resource_manager import ResourceManager, get_resource_manager

        rm = get_resource_manager()
        assert isinstance(rm, ResourceManager)

    def test_get_resource_manager_singleton(self):
        """Testa que get_resource_manager retorna sempre a mesma instância."""
        import src.utils.resource_manager as rm_module

        # Reset singleton
        rm_module._resource_manager = None

        from src.utils.resource_manager import get_resource_manager

        rm1 = get_resource_manager()
        rm2 = get_resource_manager()
        assert rm1 is rm2

    def test_get_resource_manager_reuses_existing(self):
        """Testa que get_resource_manager reutiliza instância existente."""
        import src.utils.resource_manager as rm_module
        from src.utils.resource_manager import ResourceManager, get_resource_manager

        # Set a specific instance
        existing = ResourceManager()
        rm_module._resource_manager = existing

        result = get_resource_manager()
        assert result is existing
