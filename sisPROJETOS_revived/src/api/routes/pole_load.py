"""
Rota de cálculo de esforços em postes — API REST sisPROJETOS.

Endpoint: POST /api/v1/pole-load/resultant
Calcula a resultante de forças em postes de distribuição.
"""

from fastapi import APIRouter, HTTPException

from api.schemas import PoleLoadRequest, PoleLoadResponse
from modules.pole_load.logic import PoleLoadLogic
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/pole-load", tags=["Esforços em Postes"])
_logic = PoleLoadLogic()


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
