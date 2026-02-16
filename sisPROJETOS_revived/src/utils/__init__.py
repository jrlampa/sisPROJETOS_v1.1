"""
Pacote de utilitários do sisPROJETOS.

Contém módulos reutilizáveis:
- logger: Sistema de logging centralizado
- utils: Funções auxiliares gerais
- dxf_manager: Manipulação de arquivos DXF
- model_generator: Geração de modelos
"""

import os
import sys

from .logger import LogContext, get_logger, setup_logger


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    Args:
        relative_path: Path relative to the project root

    Returns:
        str: Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)


__all__ = ["get_logger", "setup_logger", "LogContext", "resource_path"]
