"""
Camada de Domínio (DDD) do sisPROJETOS.

Contém entidades de domínio, objetos de valor (value objects), interfaces de
repositório (ports) e serviços de domínio que representam os conceitos centrais
do negócio de engenharia elétrica, independentes de infraestrutura (banco de
dados, API REST, interface gráfica).

Padrão: Domain-Driven Design (DDD) + Ports and Adapters (Hexagonal Architecture)
- Entidades: objetos com identidade (Conductor, Pole, Concessionaire)
- Value Objects: objetos imutáveis definidos por seus valores (UTMCoordinate, etc.)
- Repositories: interfaces Protocol (ports) para acesso a dados do domínio
- Services: lógica de negócio que envolve múltiplos conceitos de domínio
"""

from domain.entities import Concessionaire, Conductor, Pole
from domain.repositories import ConcessionaireRepository, ConductorRepository, PoleRepository
from domain.services import CatenaryDomainService, VoltageDropDomainService
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
]
