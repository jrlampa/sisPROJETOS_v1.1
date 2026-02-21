"""
Rota de cálculo de esforços em postes — API REST sisPROJETOS.

Endpoints:
- POST /api/v1/pole-load/resultant  — Calcula resultante de esforços em poste
- GET  /api/v1/pole-load/suggest    — Sugere postes por força resultante (sem cálculo)
"""

from fastapi import APIRouter, HTTPException, Query

from api.schemas import PoleLoadRequest, PoleLoadResponse, PoleSuggestResponse
from modules.pole_load.logic import PoleLoadLogic
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/pole-load", tags=["Esforços em Postes"])
_logic = PoleLoadLogic()


@router.get(
    "/suggest",
    response_model=PoleSuggestResponse,
    summary="Sugere postes adequados para uma carga",
    description=(
        "Consulta o catálogo de postes e retorna os de menor carga nominal que suportam "
        "a força fornecida, um por material (Concreto, Fibra de Vidro, Madeira), "
        "conforme NBR 8451/8452. Útil para integração BIM sem precisar calcular a resultante."
    ),
)
def suggest_pole(
    force_daN: float = Query(..., gt=0, description="Força resultante em daN"),
) -> PoleSuggestResponse:
    """Sugere o poste mais adequado para a carga informada."""
    try:
        suggested = _logic.suggest_pole(force_daN)
    except Exception as exc:
        logger.error("Erro ao sugerir postes para força %.2f daN: %s", force_daN, exc)
        raise HTTPException(status_code=500, detail="Erro ao consultar catálogo de postes.") from exc
    return PoleSuggestResponse(force_daN=force_daN, suggested_poles=suggested)


@router.post(
    "/resultant",
    response_model=PoleLoadResponse,
    summary="Calcula resultante de esforços em poste",
    description=(
        "Calcula a resultante vetorial de trações de condutores em um poste "
        "de distribuição elétrica, conforme metodologias Light (flecha) e Enel (tabela). "
        "Inclui sugestão de poste adequado."
    ),
)
def calculate_pole_load(request: PoleLoadRequest) -> PoleLoadResponse:
    """Calcula a resultante e sugere o poste adequado para a carga."""
    try:
        result = _logic.calculate_resultant(
            concessionaria=request.concessionaria,
            condicao=request.condicao,
            cabos_input=[c.model_dump() for c in request.cabos],
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    suggested = _logic.suggest_pole(result["resultant_force"])
    return PoleLoadResponse(
        resultant_force=result["resultant_force"],
        resultant_angle=result["resultant_angle"],
        total_x=result["total_x"],
        total_y=result["total_y"],
        vectors=result["vectors"],
        suggested_poles=suggested,
    )
