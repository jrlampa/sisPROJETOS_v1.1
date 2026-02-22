"""
Adaptadores SQLite de repositório (DDD Infrastructure — Adapters).

Implementa as interfaces Protocol definidas em `domain/repositories.py`
usando `DatabaseManager` como camada de acesso a dados. Cada adaptador
converte tuplas SQLite em entidades de domínio tipadas.

Padrão: Ports and Adapters (Hexagonal Architecture)
Referência: Eric Evans, "Domain-Driven Design" (2003), cap. 6 — Repositories
"""

from __future__ import annotations

from typing import List, Optional

from database.db_manager import DatabaseManager
from domain.entities import Concessionaire, Conductor, Pole
from domain.repositories import ConcessionaireRepository, ConductorRepository, PoleRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class SQLiteConductorRepository:
    """Adaptador SQLite para o repositório de condutores elétricos.

    Implementa `ConductorRepository` (Protocol) usando `DatabaseManager`
    como camada de persistência. Filtra registros incompletos (breaking_load=0
    ou NULL) para garantir que apenas entidades de domínio válidas sejam
    retornadas.

    Referência ABNT: NBR 7271:2004 — Condutores de alumínio para linhas aéreas.

    Args:
        db_manager: Instância configurada de `DatabaseManager`.

    Example:
        >>> repo = SQLiteConductorRepository(db_manager)
        >>> conductors = repo.get_all()
        >>> repo.get_by_name("556MCM-CA, Nu")
        Conductor(name='556MCM-CA, Nu', weight_kg_m=0.779, ...)
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def get_all(self) -> List[Conductor]:
        """Retorna todos os condutores com dados técnicos completos.

        Returns:
            Lista de entidades `Conductor` com `breaking_load_daN > 0`.
            Registros incompletos (breaking_load=0 ou NULL) são ignorados.
        """
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, weight_kg_m, breaking_load_daN, section_mm2 " "FROM conductors ORDER BY name")
            rows = cursor.fetchall()
        finally:
            conn.close()

        result: List[Conductor] = []
        for row in rows:
            entity = self._row_to_entity(row)
            if entity is not None:
                result.append(entity)
        return result

    def get_by_name(self, name: str) -> Optional[Conductor]:
        """Busca condutor por nome técnico exato.

        Args:
            name: Nome técnico do condutor (ex: '556MCM-CA, Nu').

        Returns:
            Entidade `Conductor` ou `None` se não encontrado ou incompleto.
        """
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, weight_kg_m, breaking_load_daN, section_mm2 " "FROM conductors WHERE name = ?",
                (name,),
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        return self._row_to_entity(row) if row else None

    def _row_to_entity(self, row: tuple) -> Optional[Conductor]:
        """Mapeia uma tupla do banco para uma entidade `Conductor`.

        Retorna `None` se `breaking_load_daN` for zero ou NULL (dado incompleto).
        """
        name, weight_kg_m, breaking_load_daN, section_mm2 = row
        if not (breaking_load_daN or 0) > 0:
            logger.warning("Condutor '%s' ignorado: breaking_load_daN inválido (%s)", name, breaking_load_daN)
            return None
        try:
            return Conductor(
                name=name,
                weight_kg_m=float(weight_kg_m or 0.0),
                breaking_load_daN=float(breaking_load_daN),
                section_mm2=float(section_mm2) if section_mm2 else None,
            )
        except ValueError as exc:
            logger.warning("Não foi possível criar entidade Conductor para '%s': %s", name, exc)
            return None


# Verify Protocol compliance at import time (structural subtyping)
_: ConductorRepository = SQLiteConductorRepository.__new__(SQLiteConductorRepository)


class SQLitePoleRepository:
    """Adaptador SQLite para o repositório de postes de distribuição.

    Implementa `PoleRepository` (Protocol) usando `DatabaseManager`
    como camada de persistência.

    Referência ABNT: NBR 8451:2011 — Postes de concreto armado para redes
    de distribuição de energia elétrica.

    Args:
        db_manager: Instância configurada de `DatabaseManager`.

    Example:
        >>> repo = SQLitePoleRepository(db_manager)
        >>> poles = repo.suggest_by_force(250.0)
        >>> poles[0].nominal_load_daN >= 250.0
        True
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def get_all(self) -> List[Pole]:
        """Retorna todos os postes cadastrados, ordenados por material e carga.

        Returns:
            Lista de entidades `Pole` com dados estruturais completos.
        """
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT material, height_m, format, nominal_load_daN " "FROM poles ORDER BY material, nominal_load_daN"
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        result: List[Pole] = []
        for row in rows:
            entity = self._row_to_entity(row)
            if entity is not None:
                result.append(entity)
        return result

    def suggest_by_force(self, force_daN: float) -> List[Pole]:
        """Sugere postes com carga nominal suficiente para a força aplicada.

        Retorna postes com `nominal_load_daN >= force_daN`, ordenados por
        carga crescente (menor poste adequado primeiro), conforme recomendação
        de dimensionamento da NBR 8451.

        Args:
            force_daN: Força resultante calculada em daN.

        Returns:
            Lista ordenada de entidades `Pole` adequadas para a força.
        """
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT material, height_m, format, nominal_load_daN "
                "FROM poles WHERE nominal_load_daN >= ? ORDER BY nominal_load_daN",
                (force_daN,),
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        result: List[Pole] = []
        for row in rows:
            entity = self._row_to_entity(row)
            if entity is not None:
                result.append(entity)
        return result

    def _row_to_entity(self, row: tuple) -> Optional[Pole]:
        """Mapeia uma tupla do banco para uma entidade `Pole`.

        Retorna `None` se `height_m` ou `nominal_load_daN` forem zero/NULL.
        """
        material, height_m, fmt, nominal_load_daN = row
        if not (height_m or 0) > 0 or not (nominal_load_daN or 0) > 0:
            logger.warning("Poste '%s' ignorado: altura ou carga inválida", material)
            return None
        try:
            return Pole(
                material=material,
                height_m=float(height_m),
                format=fmt or "Circular",
                nominal_load_daN=float(nominal_load_daN),
            )
        except ValueError as exc:  # pragma: no cover — early-return in _row_to_entity pre-filters identical conditions
            logger.warning("Não foi possível criar entidade Pole para '%s': %s", material, exc)
            return None


# Verify Protocol compliance at import time (structural subtyping)
__p: PoleRepository = SQLitePoleRepository.__new__(SQLitePoleRepository)


class SQLiteConcessionaireRepository:
    """Adaptador SQLite para o repositório de concessionárias de energia.

    Implementa `ConcessionaireRepository` (Protocol) usando `DatabaseManager`
    como camada de persistência.

    Args:
        db_manager: Instância configurada de `DatabaseManager`.

    Example:
        >>> repo = SQLiteConcessionaireRepository(db_manager)
        >>> light = repo.get_by_name("Light")
        >>> light.method
        'flecha'
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def get_all(self) -> List[Concessionaire]:
        """Retorna todas as concessionárias cadastradas, ordenadas por nome.

        Returns:
            Lista de entidades `Concessionaire` com método de cálculo.
        """
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, method FROM concessionaires ORDER BY name")
            rows = cursor.fetchall()
        finally:
            conn.close()

        result: List[Concessionaire] = []
        for row in rows:
            entity = self._row_to_entity(row)
            if entity is not None:
                result.append(entity)
        return result

    def get_by_name(self, name: str) -> Optional[Concessionaire]:
        """Busca concessionária por nome exato.

        Args:
            name: Nome da concessionária (ex: 'Light', 'Enel').

        Returns:
            Entidade `Concessionaire` ou `None` se não encontrada.
        """
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, method FROM concessionaires WHERE name = ?",
                (name,),
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        return self._row_to_entity(row) if row else None

    def _row_to_entity(self, row: tuple) -> Optional[Concessionaire]:
        """Mapeia uma tupla do banco para uma entidade `Concessionaire`."""
        name, method = row
        try:
            return Concessionaire(name=name, method=method)
        except ValueError as exc:
            logger.warning("Não foi possível criar entidade Concessionaire para '%s': %s", name, exc)
            return None


# Verify Protocol compliance at import time (structural subtyping)
__c: ConcessionaireRepository = SQLiteConcessionaireRepository.__new__(SQLiteConcessionaireRepository)
