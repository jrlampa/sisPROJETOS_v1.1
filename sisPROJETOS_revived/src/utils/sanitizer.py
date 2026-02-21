"""
Módulo de sanitização e validação de dados para sisPROJETOS.

Fornece funções reutilizáveis para validar e sanitizar entradas
de usuário em toda a aplicação, seguindo os princípios de segurança
e conformidade com normas técnicas brasileiras (ABNT NBR 5410).

Responsabilidade Única: Sanitização/validação de dados de entrada.
Zero dependências externas (apenas stdlib).

Uso:
    from utils.sanitizer import sanitize_string, sanitize_numeric

    name = sanitize_string(user_input, max_length=100)
    value = sanitize_numeric(raw_value, min_val=0.0, default=0.0)
"""

import os
import re
import unicodedata
from typing import Any, Optional, Sequence


def sanitize_string(
    value: Any,
    max_length: int = 255,
    allow_empty: bool = False,
    strip: bool = True,
) -> str:
    """Sanitiza uma string removendo caracteres de controle e limitando o tamanho.

    Args:
        value: Valor de entrada (qualquer tipo, convertido para str).
        max_length: Comprimento máximo permitido (padrão: 255).
        allow_empty: Se False, levanta ValueError quando a string for vazia.
        strip: Se True, remove espaços em branco nas extremidades.

    Returns:
        str: String sanitizada e normalizada (NFC Unicode).

    Raises:
        ValueError: Se a string resultante for vazia e allow_empty=False.

    Example:
        >>> sanitize_string("  João\\x00  ", max_length=50)
        'João'
    """
    if value is None:
        text = ""
    else:
        text = str(value)

    # Remove null bytes e caracteres de controle (exceto tab/newline)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalização Unicode NFC (composta) para consistência
    text = unicodedata.normalize("NFC", text)

    if strip:
        text = text.strip()

    # Truncar para tamanho máximo
    if max_length > 0:
        text = text[:max_length]

    if not allow_empty and not text:
        raise ValueError("Valor de texto não pode ser vazio")

    return text


def sanitize_numeric(
    value: Any,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    default: Optional[float] = None,
) -> float:
    """Converte e valida um valor numérico dentro de um intervalo.

    Args:
        value: Valor a converter para float.
        min_val: Valor mínimo permitido (inclusive). Sem limite se None.
        max_val: Valor máximo permitido (inclusive). Sem limite se None.
        default: Valor retornado se a conversão falhar. Levanta ValueError se None.

    Returns:
        float: Valor numérico validado.

    Raises:
        ValueError: Se a conversão falhar e default=None, ou se o valor
                    estiver fora do intervalo [min_val, max_val].

    Example:
        >>> sanitize_numeric("42.5", min_val=0.0, max_val=100.0)
        42.5
    """
    try:
        result = float(value)
    except (TypeError, ValueError):
        if default is not None:
            return float(default)
        raise ValueError(f"Valor inválido: '{value}' não é numérico")

    if min_val is not None and result < min_val:
        raise ValueError(f"Valor {result} abaixo do mínimo permitido ({min_val})")
    if max_val is not None and result > max_val:
        raise ValueError(f"Valor {result} acima do máximo permitido ({max_val})")

    return result


def sanitize_positive(value: Any, default: Optional[float] = None) -> float:
    """Valida que o valor é estritamente positivo (> 0).

    Args:
        value: Valor a validar.
        default: Retornado se conversão falhar. Levanta ValueError se None.

    Returns:
        float: Valor positivo.

    Raises:
        ValueError: Se o valor for zero ou negativo.

    Example:
        >>> sanitize_positive("10.5")
        10.5
    """
    result = sanitize_numeric(value, default=default)
    if result <= 0:
        raise ValueError(f"Valor deve ser positivo (> 0). Recebido: {result}")
    return result


def sanitize_power_factor(value: Any) -> float:
    """Valida o fator de potência (cos φ) conforme NBR 5410.

    Intervalo válido: 0 < cos_phi ≤ 1.

    Args:
        value: Fator de potência a validar.

    Returns:
        float: Fator de potência validado.

    Raises:
        ValueError: Se o valor estiver fora do intervalo (0, 1].

    Example:
        >>> sanitize_power_factor(0.92)
        0.92
    """
    result = sanitize_numeric(value)
    if not (0 < result <= 1):
        raise ValueError(
            f"Fator de potência (cos φ) deve estar entre 0 (exclusivo) e 1 (inclusivo). " f"Recebido: {result}"
        )
    return result


def sanitize_phases(value: Any) -> int:
    """Valida o número de fases (deve ser 1 ou 3) conforme NBR 5410.

    Args:
        value: Número de fases a validar.

    Returns:
        int: Número de fases validado (1 ou 3).

    Raises:
        ValueError: Se o valor não for 1 ou 3.

    Example:
        >>> sanitize_phases(3)
        3
    """
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Número de fases inválido: '{value}'")

    if result not in (1, 3):
        raise ValueError(f"Número de fases deve ser 1 ou 3. Recebido: {result}")
    return result


def sanitize_filepath(
    filepath: Any,
    allowed_extensions: Optional[Sequence[str]] = None,
) -> str:
    """Sanitiza e valida um caminho de arquivo.

    Verifica:
    - Não é vazio/None
    - Não contém bytes nulos
    - Extensão pertence à lista permitida (se informada)

    Não resolve o caminho absoluto (deixa para o chamador).

    Args:
        filepath: Caminho de arquivo a validar.
        allowed_extensions: Lista de extensões permitidas (ex: ['.dxf', '.xlsx']).
                            Sem restrição se None ou vazio.

    Returns:
        str: Caminho sanitizado (sem bytes nulos, strip aplicado).

    Raises:
        ValueError: Se o caminho for inválido, nulo ou extensão não permitida.

    Example:
        >>> sanitize_filepath("output.dxf", [".dxf", ".dwg"])
        'output.dxf'
    """
    if filepath is None or not isinstance(filepath, str):
        raise ValueError("Caminho de arquivo deve ser uma string não nula")

    path = filepath.strip()

    if not path:
        raise ValueError("Caminho de arquivo não pode ser vazio")

    if "\x00" in path:
        raise ValueError("Caminho de arquivo contém bytes nulos inválidos")

    if allowed_extensions:
        _, ext = os.path.splitext(path)
        ext_lower = ext.lower()
        allowed_lower = [e.lower() for e in allowed_extensions]
        if ext_lower not in allowed_lower:
            raise ValueError(f"Extensão '{ext}' não permitida. Use: {', '.join(allowed_extensions)}")

    return path


def sanitize_code(value: Any, max_length: int = 30) -> str:
    """Sanitiza um código de projeto/identificador alfanumérico.

    Permite apenas letras, números, hifens e underscores.
    Converte para maiúsculas para padronização.

    Args:
        value: Código a sanitizar.
        max_length: Comprimento máximo (padrão: 30).

    Returns:
        str: Código sanitizado em maiúsculas.

    Raises:
        ValueError: Se o código for inválido ou vazio após sanitização.

    Example:
        >>> sanitize_code("ZX-323948246")
        'ZX-323948246'
    """
    text = sanitize_string(value, max_length=max_length, allow_empty=False)

    # Permite apenas alfanuméricos, hifens e underscores
    cleaned = re.sub(r"[^A-Za-z0-9\-_]", "", text)

    if not cleaned:
        raise ValueError(f"Código '{value}' não contém caracteres válidos (use letras, números, - ou _)")

    return cleaned.upper()
