"""
Camada de Infraestrutura (DDD) do sisPROJETOS.

Contém os adaptadores concretos (Adapters) que implementam as interfaces de
repositório (Ports) definidas em `src/domain/repositories.py`.

Padrão: Ports and Adapters (Hexagonal Architecture)
  - Ports: interfaces Protocol em `src/domain/repositories.py`
  - Adapters: implementações SQLite neste pacote

Os adaptadores traduzem entre a representação relacional do banco de dados
e as entidades de domínio, garantindo que o domínio nunca dependa de detalhes
de infraestrutura.
"""

from infrastructure.repositories import (
    SQLiteConcessionaireRepository,
    SQLiteConductorRepository,
    SQLitePoleRepository,
)

__all__ = [
    "SQLiteConductorRepository",
    "SQLitePoleRepository",
    "SQLiteConcessionaireRepository",
]
