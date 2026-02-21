"""
Sistema de logging centralizado para sisPROJETOS.

Fornece configuração unificada de logging com:
- Rotating file handler (logs em AppData)
- Console handler (desenvolvimento)
- Formatação padronizada
- Níveis de log configuráveis via .env
- Context manager para log de operações

Uso:
    from utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Operação iniciada")
    logger.error("Erro ao processar", exc_info=True)
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def get_app_data_path() -> Path:
    """
    Retorna o caminho do diretório de dados do aplicativo.

    Windows: %APPDATA%/sisPROJETOS/
    Linux/Mac: ~/.local/share/sisPROJETOS/

    Returns:
        Path: Caminho absoluto para o diretório de dados
    """
    if sys.platform == "win32":  # pragma: no cover
        base_path = os.getenv("APPDATA", os.path.expanduser("~"))
    else:
        base_path = os.path.expanduser("~/.local/share")

    app_data = Path(base_path) / "sisPROJETOS"
    app_data.mkdir(parents=True, exist_ok=True)

    return app_data


def get_log_path() -> Path:
    """
    Retorna o caminho do diretório de logs.

    Pode ser sobrescrito via variável de ambiente LOG_PATH.

    Returns:
        Path: Caminho absoluto para o diretório de logs
    """
    custom_path = os.getenv("LOG_PATH")

    if custom_path:
        log_path = Path(custom_path)
    else:
        log_path = get_app_data_path() / "logs"

    log_path.mkdir(parents=True, exist_ok=True)

    return log_path


def setup_logger(
    name: str, level: Optional[str] = None, log_to_file: bool = True, log_to_console: bool = None
) -> logging.Logger:
    """
    Configura e retorna um logger com handlers apropriados.

    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Default: Lê de .env (LOG_LEVEL) ou INFO
        log_to_file: Se True, loga para arquivo rotativo
        log_to_console: Se True, loga para console. Default: True se DEBUG=True

    Returns:
        logging.Logger: Logger configurado

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Aplicação iniciada")
    """
    logger = logging.getLogger(name)

    # Evita duplicação de handlers
    if logger.handlers:
        return logger

    # Determina nível de log
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    logger.setLevel(getattr(logging, level, logging.INFO))

    # Formato de log
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler de arquivo (rotating)
    if log_to_file:
        log_file = get_log_path() / "sisprojetos.log"

        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10 MB
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Handler de console (desenvolvimento)
    if log_to_console is None:
        log_to_console = os.getenv("DEBUG", "False").lower() == "true"

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Atalho para obter um logger configurado.

    Args:
        name: Nome do logger (geralmente __name__)

    Returns:
        logging.Logger: Logger configurado

    Example:
        >>> from utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Mensagem de log")
    """
    return setup_logger(name)


class LogContext:
    """
    Context manager para log de operações com tempo de execução.

    Example:
        >>> logger = get_logger(__name__)
        >>> with LogContext(logger, "Processando arquivo XYZ"):
        ...     processar_arquivo()
        # Logs:
        # 2026-02-16 10:00:00 | INFO | module | Processando arquivo XYZ...
        # 2026-02-16 10:00:05 | INFO | module | Processando arquivo XYZ concluído (5.2s)
    """

    def __init__(self, logger: logging.Logger, operation: str, level: int = logging.INFO):
        """
        Args:
            logger: Logger a ser usado
            operation: Descrição da operação
            level: Nível de log (logging.INFO, logging.DEBUG, etc.)
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None

    def __enter__(self):
        """Inicia o contexto e loga início da operação."""
        import time

        self.start_time = time.time()
        self.logger.log(self.level, f"{self.operation}...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Finaliza o contexto e loga resultado.

        Se houver exceção, loga como ERROR.
        Caso contrário, loga conclusão com tempo decorrido.
        """
        import time

        elapsed = time.time() - self.start_time

        if exc_type is not None:
            self.logger.error(f"{self.operation} falhou após {elapsed:.1f}s: {exc_val}", exc_info=True)
        else:
            self.logger.log(self.level, f"{self.operation} concluído ({elapsed:.1f}s)")

        # Não suprime exceções
        return False


# Logger padrão da aplicação
app_logger = get_logger("sisPROJETOS")


if __name__ == "__main__":
    # Testes básicos do sistema de logging
    print("=" * 60)
    print("Teste do Sistema de Logging")
    print("=" * 60)

    # Teste 1: Logger básico
    logger = get_logger("test_module")
    logger.debug("Mensagem de DEBUG")
    logger.info("Mensagem de INFO")
    logger.warning("Mensagem de WARNING")
    logger.error("Mensagem de ERROR")
    logger.critical("Mensagem de CRITICAL")

    print(f"\nArquivo de log: {get_log_path() / 'sisprojetos.log'}")

    # Teste 2: Context manager
    print("\n" + "=" * 60)
    print("Teste do LogContext")
    print("=" * 60)

    import time

    with LogContext(logger, "Operação de teste"):
        time.sleep(0.5)

    # Teste 3: Exception handling
    try:
        with LogContext(logger, "Operação com erro", level=logging.WARNING):
            raise ValueError("Erro simulado para teste")
    except ValueError:
        pass

    print("\n✅ Testes concluídos. Verifique o arquivo de log.")
