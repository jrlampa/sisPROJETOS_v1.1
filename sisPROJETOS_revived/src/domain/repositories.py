"""
Interfaces de repositório do domínio sisPROJETOS (DDD Ports).

Define os contratos (Protocolos) que as implementações de infraestrutura
devem satisfazer para fornecer acesso a dados do domínio.

Padrão: Ports and Adapters (Hexagonal Architecture)
  - Ports: as interfaces Protocol definidas neste módulo
  - Adapters: implementações em src/database/ (DatabaseManager)

Referências:
    - Eric Evans, "Domain-Driven Design" (2003), cap. 6 — Repositories
    - ABNT ISO/IEC 25010:2023 — Qualidade de Software (Maintainability)
"""

from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from domain.entities import Concessionaire, Conductor, Pole


@runtime_checkable
class ConductorRepository(Protocol):
    """Protocolo de repositório para condutores elétricos.

    Define a interface que qualquer adaptador de infraestrutura deve implementar
    para fornecer acesso ao catálogo de condutores da rede de distribuição.
    """

    def get_all(self) -> List[Conductor]:
        """Retorna todos os condutores cadastrados.

        Returns:
            Lista de entidades Conductor com dados técnicos completos.
        """
        ...  # pragma: no cover

    def get_by_name(self, name: str) -> Optional[Conductor]:
        """Busca condutor por nome técnico.

        Args:
            name: Nome técnico do condutor (ex: '556MCM-CA', '1/0AWG-CAA').

        Returns:
            Entidade Conductor ou None se não encontrado.
        """
        ...  # pragma: no cover


@runtime_checkable
class PoleRepository(Protocol):
    """Protocolo de repositório para postes de distribuição.

    Define a interface para acesso ao catálogo de postes com suas
    características estruturais (material, altura, carga nominal),
    conforme NBR 8451.
    """

    def get_all(self) -> List[Pole]:
        """Retorna todos os postes cadastrados.

        Returns:
            Lista de entidades Pole com características estruturais completas.
        """
        ...  # pragma: no cover

    def suggest_by_force(self, force_daN: float) -> List[Pole]:
        """Sugere postes compatíveis com a força resultante calculada.

        Args:
            force_daN: Força resultante em daN que o poste deve suportar.

        Returns:
            Lista de entidades Pole com carga nominal >= force_daN,
            ordenada por carga nominal crescente (menor adequado primeiro).
        """
        ...  # pragma: no cover


@runtime_checkable
class ConcessionaireRepository(Protocol):
    """Protocolo de repositório para concessionárias de energia.

    Define a interface para acesso ao cadastro de concessionárias e seus
    métodos de cálculo de projetos de distribuição elétrica.
    """

    def get_all(self) -> List[Concessionaire]:
        """Retorna todas as concessionárias cadastradas.

        Returns:
            Lista de entidades Concessionaire com método de cálculo.
        """
        ...  # pragma: no cover

    def get_by_name(self, name: str) -> Optional[Concessionaire]:
        """Busca concessionária por nome.

        Args:
            name: Nome da concessionária (ex: 'Light', 'Enel').

        Returns:
            Entidade Concessionaire ou None se não encontrada.
        """
        ...  # pragma: no cover
