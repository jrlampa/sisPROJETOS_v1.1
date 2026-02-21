"""
Rota de cálculo de catenária — API REST sisPROJETOS.

Endpoint: POST /api/v1/catenary/calculate
Calcula flecha e constante catenária conforme NBR 5422.
"""

from fastapi import APIRouter, HTTPException
from api.schemas import CatenaryRequest, CatenaryResponse
from modules.catenaria.logic import CatenaryLogic
from utils.logger import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/catenary", tags=["Catenária"])
_logic = CatenaryLogic()


@router.post(
    "/calculate",
    response_model=CatenaryResponse,
    summary="Calcula catenária de condutor (NBR 5422)",
    description=(
        "Calcula a flecha máxima e a constante catenária de um condutor "
        "suspenso entre dois apoios, conforme NBR 5422. "
        "Suporta vãos inclinados (ha ≠ hb)."
    ),
)
def calculate_catenary(request: CatenaryRequest) -> CatenaryResponse:
    """Calcula parâmetros da catenária e retorna flecha e constante."""
    result = _logic.calculate_catenary(
        span=request.span,
        ha=request.ha,
        hb=request.hb,
        tension_daN=request.tension_daN,
        weight_kg_m=request.weight_kg_m,
    )
    if result is None:
        logger.warning("Cálculo de catenária retornou None para %s", request.model_dump())
        raise HTTPException(status_code=422, detail="Peso linear zero ou dados inválidos para o cálculo.")
    return CatenaryResponse(
        sag=float(result["sag"]),
        tension=float(result["tension"]),
        catenary_constant=float(result["catenary_constant"]),
    )
