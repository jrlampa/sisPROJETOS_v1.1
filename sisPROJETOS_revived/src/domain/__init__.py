"""
Camada de Domínio (DDD) do sisPROJETOS.

Contém entidades de domínio, objetos de valor (value objects), interfaces de
repositório (ports), serviços de domínio e padrões regulatórios que representam
os conceitos centrais do negócio de engenharia elétrica, independentes de
infraestrutura (banco de dados, API REST, interface gráfica).

Padrão: Domain-Driven Design (DDD) + Ports and Adapters (Hexagonal Architecture)
- Entidades: objetos com identidade (Conductor, Pole, Concessionaire)
- Value Objects: objetos imutáveis definidos por seus valores (UTMCoordinate, etc.)
- Repositories: interfaces Protocol (ports) para acesso a dados do domínio
- Services: lógica de negócio que envolve múltiplos conceitos de domínio
- Standards: padrões regulatórios ABNT, ANEEL/PRODIST e concessionárias
"""

from domain.entities import Concessionaire, Conductor, Pole
from domain.repositories import ConcessionaireRepository, ConductorRepository, PoleRepository
from domain.services import CatenaryDomainService, VoltageDropDomainService
from domain.standards import (
    ALL_STANDARDS,
    ENEL_BT,
    LIGHT_BT,
    NBR_5410,
    PRODIST_MODULE8_BT,
    PRODIST_MODULE8_MT,
    VoltageStandard,
    get_standard_by_name,
)
from domain.value_objects import CatenaryResult, SpanResult, UTMCoordinate, VoltageDropResult

__all__ = [
    # Entidades
    "Conductor",
    "Pole",
    "Concessionaire",
    # Value Objects
    "UTMCoordinate",
    "CatenaryResult",
    "VoltageDropResult",
    "SpanResult",
    # Repositories (Ports)
    "ConductorRepository",
    "PoleRepository",
    "ConcessionaireRepository",
    # Domain Services
    "CatenaryDomainService",
    "VoltageDropDomainService",
    # Padrões Regulatórios (ABNT / ANEEL/PRODIST / Concessionárias)
    "VoltageStandard",
    "NBR_5410",
    "PRODIST_MODULE8_BT",
    "PRODIST_MODULE8_MT",
    "LIGHT_BT",
    "ENEL_BT",
    "ALL_STANDARDS",
    "get_standard_by_name",
]
