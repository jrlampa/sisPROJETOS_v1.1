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

    Raises:
        ValueError: If path contains directory traversal attempts
    """
    # Validate path to prevent path traversal
    if relative_path and (".." in relative_path or relative_path.startswith("/")):
        raise ValueError(f"Invalid path: path traversal not allowed in '{relative_path}'")

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    full_path = os.path.join(base_path, relative_path)

    # Additional security: ensure resolved path is within base_path
    real_base = os.path.realpath(base_path)
    real_full = os.path.realpath(full_path)

    if not real_full.startswith(real_base):
        raise ValueError(f"Path traversal detected: '{relative_path}' resolves outside base directory")

    return full_path


__all__ = ["get_logger", "setup_logger", "LogContext", "resource_path"]
