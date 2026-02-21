"""
Rota de dados mestres — API REST sisPROJETOS.

Endpoints de consulta (GET) para dados cadastrais do banco de dados:
  - GET /api/v1/data/conductors
  - GET /api/v1/data/poles
  - GET /api/v1/data/concessionaires

Esses endpoints expõem os catálogos técnicos para integração com
ferramentas BIM (Half-way BIM) e outros sistemas externos.
Todos os dados são somente leitura (sem custo, zero mocks — DB local SQLite).
"""

from typing import List

from fastapi import APIRouter, HTTPException

from api.schemas import ConcessionaireOut, ConductorOut, PoleOut
from database.db_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/data", tags=["Dados Mestres"])
_db = DatabaseManager()


@router.get(
    "/conductors",
    response_model=List[ConductorOut],
    summary="Lista condutores elétricos cadastrados",
    description=(
        "Retorna o catálogo completo de condutores elétricos disponíveis "
        "no banco de dados do sisPROJETOS, com nome e peso linear (kg/m). "
        "Útil para integração com ferramentas BIM e planilhas de dimensionamento."
    ),
)
def list_conductors() -> List[ConductorOut]:
    """Lista todos os condutores cadastrados no banco de dados."""
    try:
        rows = _db.get_all_conductors()
    except Exception as exc:
        logger.error("Erro ao listar condutores: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao consultar condutores no banco de dados.") from exc
    return [ConductorOut(name=row[0], weight_kg_m=float(row[1])) for row in rows]


@router.get(
    "/poles",
    response_model=List[PoleOut],
    summary="Lista postes de distribuição cadastrados",
    description=(
        "Retorna o catálogo completo de postes de distribuição elétrica, "
        "incluindo material, formato, descrição e carga nominal em daN. "
        "Referência para projetos conforme NBR 8451."
    ),
)
def list_poles() -> List[PoleOut]:
    """Lista todos os postes cadastrados no banco de dados."""
    try:
        rows = _db.get_all_poles()
    except Exception as exc:
        logger.error("Erro ao listar postes: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao consultar postes no banco de dados.") from exc
    return [
        PoleOut(
            material=row[0],
            format=row[1],
            description=row[2],
            nominal_load_daN=float(row[3]),
        )
        for row in rows
    ]


@router.get(
    "/concessionaires",
    response_model=List[ConcessionaireOut],
    summary="Lista concessionárias de energia cadastradas",
    description=(
        "Retorna as concessionárias de energia elétrica cadastradas "
        "no sistema, junto ao método de cálculo de esforços utilizado "
        "(flecha para Light, tabela para Enel)."
    ),
)
def list_concessionaires() -> List[ConcessionaireOut]:
    """Lista todas as concessionárias cadastradas no banco de dados."""
    try:
        rows = _db.get_all_concessionaires()
    except Exception as exc:
        logger.error("Erro ao listar concessionárias: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao consultar concessionárias no banco de dados.") from exc
    return [ConcessionaireOut(name=row[0], method=row[1]) for row in rows]
