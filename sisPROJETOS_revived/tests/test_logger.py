"""
Testes para o sistema de logging centralizado.

Testa:
- Configuração de logger
- Rotação de arquivos
- Níveis de log
- Context manager
- Path resolution
"""

import logging
import os
import tempfile
import time
from pathlib import Path

import pytest

from src.utils.logger import (
    LogContext,
    get_app_data_path,
    get_log_path,
    get_logger,
    setup_logger,
)


class TestLoggerSetup:
    """Testes de configuração do sistema de logging."""
    
    def test_get_app_data_path_exists(self):
        """Verifica se o caminho do AppData é criado."""
        path = get_app_data_path()
        assert path.exists()
        assert path.is_dir()
        assert "sisPROJETOS" in str(path)
    
    def test_get_log_path_exists(self):
        """Verifica se o diretório de logs é criado."""
        path = get_log_path()
        assert path.exists()
        assert path.is_dir()
        assert "logs" in str(path)
    
    def test_get_log_path_custom(self, monkeypatch, tmp_path):
        """Testa sobrescrita do path via variável de ambiente."""
        custom_path = tmp_path / "custom_logs"
        monkeypatch.setenv("LOG_PATH", str(custom_path))
        
        path = get_log_path()
        assert path == custom_path
        assert path.exists()
    
    def test_setup_logger_creates_logger(self):
        """Verifica se setup_logger cria um logger válido."""
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_setup_logger_default_level(self):
        """Verifica nível padrão de log (INFO)."""
        logger = setup_logger("test_default_level", log_to_file=False)
        assert logger.level == logging.INFO
    
    def test_setup_logger_custom_level(self):
        """Testa configuração de nível customizado."""
        logger = setup_logger("test_custom_level", level="DEBUG", log_to_file=False)
        assert logger.level == logging.DEBUG
    
    def test_setup_logger_from_env(self, monkeypatch):
        """Testa leitura de nível de log da variável de ambiente."""
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        logger = setup_logger("test_env_level", log_to_file=False)
        assert logger.level == logging.WARNING
    
    def test_get_logger_shortcut(self):
        """Verifica se get_logger funciona como atalho."""
        logger = get_logger("test_shortcut")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_shortcut"


class TestFileLogging:
    """Testes de logging para arquivo."""
    
    def test_log_file_is_created(self):
        """Verifica se o arquivo de log é criado."""
        logger = setup_logger("test_file_creation")
        logger.info("Test message")
        
        log_file = get_log_path() / "sisprojetos.log"
        assert log_file.exists()
    
    def test_log_file_contains_message(self):
        """Verifica se mensagens são escritas no arquivo."""
        logger = setup_logger("test_file_content")
        test_message = f"Test message {time.time()}"
        logger.info(test_message)
        
        # Força flush dos handlers
        for handler in logger.handlers:
            handler.flush()
        
        log_file = get_log_path() / "sisprojetos.log"
        content = log_file.read_text(encoding="utf-8")
        
        assert test_message in content
    
    def test_log_format(self):
        """Verifica formato de log (timestamp | level | name | message)."""
        logger = setup_logger("test_format")
        test_message = f"Format test {time.time()}"
        logger.warning(test_message)
        
        for handler in logger.handlers:
            handler.flush()
        
        log_file = get_log_path() / "sisprojetos.log"
        content = log_file.read_text(encoding="utf-8")
        
        # Verifica se contém os componentes do formato
        assert "WARNING" in content
        assert "test_format" in content
        assert test_message in content
        assert "|" in content  # Separador de campos
    
    def test_no_file_logging_when_disabled(self, tmp_path):
        """Verifica que não cria arquivo quando log_to_file=False."""
        logger = setup_logger(
            "test_no_file",
            log_to_file=False,
            log_to_console=False
        )
        logger.info("Should not be in file")
        
        # Não deve haver handlers de arquivo
        file_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 0


class TestConsoleLogging:
    """Testes de logging para console."""
    
    def test_console_logging_in_debug_mode(self, monkeypatch):
        """Verifica que console logging é ativado em modo DEBUG."""
        monkeypatch.setenv("DEBUG", "True")
        logger = setup_logger("test_console_debug", log_to_file=False)
        
        console_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        ]
        assert len(console_handlers) > 0
    
    def test_no_console_logging_by_default(self, monkeypatch):
        """Verifica que console logging não é ativado por padrão."""
        monkeypatch.setenv("DEBUG", "False")
        logger = setup_logger("test_no_console", log_to_file=False)
        
        console_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        ]
        assert len(console_handlers) == 0
    
    def test_console_logging_explicit(self):
        """Testa ativação explícita de console logging."""
        logger = setup_logger(
            "test_console_explicit",
            log_to_file=False,
            log_to_console=True
        )
        
        console_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        ]
        assert len(console_handlers) > 0


class TestLogLevels:
    """Testes de níveis de log."""
    
    def test_debug_level(self):
        """Teste de mensagens DEBUG."""
        logger = setup_logger("test_debug", level="DEBUG", log_to_file=False)
        assert logger.isEnabledFor(logging.DEBUG)
    
    def test_info_level(self):
        """Teste de mensagens INFO."""
        logger = setup_logger("test_info", level="INFO", log_to_file=False)
        assert logger.isEnabledFor(logging.INFO)
        assert not logger.isEnabledFor(logging.DEBUG)
    
    def test_warning_level(self):
        """Teste de mensagens WARNING."""
        logger = setup_logger("test_warning", level="WARNING", log_to_file=False)
        assert logger.isEnabledFor(logging.WARNING)
        assert not logger.isEnabledFor(logging.INFO)
    
    def test_error_level(self):
        """Teste de mensagens ERROR."""
        logger = setup_logger("test_error", level="ERROR", log_to_file=False)
        assert logger.isEnabledFor(logging.ERROR)
        assert not logger.isEnabledFor(logging.WARNING)
    
    def test_critical_level(self):
        """Teste de mensagens CRITICAL."""
        logger = setup_logger("test_critical", level="CRITICAL", log_to_file=False)
        assert logger.isEnabledFor(logging.CRITICAL)
        assert not logger.isEnabledFor(logging.ERROR)


class TestLogContext:
    """Testes do context manager LogContext."""
    
    def test_log_context_success(self, caplog):
        """Testa LogContext com operação bem-sucedida."""
        logger = get_logger("test_context_success")
        
        with caplog.at_level(logging.INFO):
            with LogContext(logger, "Test operation"):
                time.sleep(0.1)
        
        # Verifica mensagens de início e fim
        assert "Test operation..." in caplog.text
        assert "Test operation concluído" in caplog.text
        assert "0.1s" in caplog.text or "0.2s" in caplog.text  # Tolerância
    
    def test_log_context_with_exception(self, caplog):
        """Testa LogContext com exceção."""
        logger = get_logger("test_context_exception")
        
        with caplog.at_level(logging.ERROR):
            try:
                with LogContext(logger, "Operation with error"):
                    raise ValueError("Test error")
            except ValueError:
                pass
        
        # Verifica mensagem de erro
        assert "Operation with error falhou" in caplog.text
        assert "Test error" in caplog.text
    
    def test_log_context_custom_level(self, caplog):
        """Testa LogContext com nível customizado."""
        logger = setup_logger("test_context_level_custom", level="DEBUG", log_to_file=False)
        
        with caplog.at_level(logging.DEBUG):
            with LogContext(logger, "Debug operation", level=logging.DEBUG):
                pass
        
        assert "Debug operation..." in caplog.text
    
    def test_log_context_timing_accuracy(self, caplog):
        """Verifica precisão da medição de tempo."""
        logger = get_logger("test_context_timing")
        
        with caplog.at_level(logging.INFO):
            with LogContext(logger, "Timed operation"):
                time.sleep(0.5)
        
        # Deve reportar ~0.5s (com tolerância)
        assert "0.5s" in caplog.text or "0.6s" in caplog.text


class TestHandlerDuplication:
    """Testes para evitar duplicação de handlers."""
    
    def test_no_duplicate_handlers(self):
        """Verifica que chamar setup_logger duas vezes não duplica handlers."""
        logger1 = setup_logger("test_duplicate", log_to_file=False)
        handler_count_1 = len(logger1.handlers)
        
        logger2 = setup_logger("test_duplicate", log_to_file=False)
        handler_count_2 = len(logger2.handlers)
        
        assert logger1 is logger2  # Mesmo objeto
        assert handler_count_1 == handler_count_2  # Mesma quantidade de handlers


class TestEdgeCases:
    """Testes de casos limites."""
    
    def test_unicode_messages(self):
        """Testa mensagens com caracteres Unicode."""
        logger = get_logger("test_unicode")
        
        # Não deve lançar exceção
        logger.info("Teste com acentuação: áéíóú çñ")
        logger.warning("Símbolos: ⚡ 🔌 📊")
        logger.error("Emoji: 😀 🎉")
    
    def test_very_long_message(self):
        """Testa mensagens muito longas."""
        logger = get_logger("test_long")
        long_message = "x" * 10000
        
        # Não deve lançar exceção
        logger.info(long_message)
    
    def test_multiline_message(self):
        """Testa mensagens multilinha."""
        logger = get_logger("test_multiline")
        
        multiline = """Linha 1
        Linha 2
        Linha 3"""
        
        logger.info(multiline)
    
    def test_exception_logging(self):
        """Testa logging de exceções com traceback."""
        logger = get_logger("test_exception")
        
        try:
            1 / 0
        except ZeroDivisionError:
            # Não deve lançar exceção
            logger.error("Division by zero", exc_info=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
