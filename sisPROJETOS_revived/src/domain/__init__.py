"""
Camada de Domínio (DDD) do sisPROJETOS.

Contém entidades de domínio e objetos de valor (value objects) que representam
os conceitos centrais do negócio de engenharia elétrica, independentes de
infraestrutura (banco de dados, API REST, interface gráfica).

Padrão: Domain-Driven Design (DDD)
- Entidades: objetos com identidade (Conductor, Pole, Concessionaire)
- Value Objects: objetos imutáveis definidos por seus valores (UTMCoordinate, etc.)
"""

from domain.entities import Conductor, Concessionaire, Pole
from domain.value_objects import CatenaryResult, SpanResult, UTMCoordinate, VoltageDropResult

__all__ = [
    "Conductor",
    "Pole",
    "Concessionaire",
    "UTMCoordinate",
    "CatenaryResult",
    "VoltageDropResult",
    "SpanResult",
]
