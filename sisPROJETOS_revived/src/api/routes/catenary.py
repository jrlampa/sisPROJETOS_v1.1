"""
Rota de cálculo de catenária — API REST sisPROJETOS.

Endpoint: POST /api/v1/catenary/calculate
Calcula flecha e constante catenária conforme NBR 5422.
Suporta verificação opcional de folga ao solo (min_clearance_m).
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from api.schemas import CatenaryRequest, CatenaryResponse
from domain.services import CatenaryDomainService
from domain.value_objects import CatenaryResult
from modules.catenaria.logic import CatenaryLogic
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/catenary", tags=["Catenária"])
_logic = CatenaryLogic()
_domain_service = CatenaryDomainService()


@router.post(
    "/calculate",
    response_model=CatenaryResponse,
    summary="Calcula catenária de condutor (NBR 5422)",
    description=(
        "Calcula a flecha máxima e a constante catenária de um condutor "
        "suspenso entre dois apoios, conforme NBR 5422. "
        "Suporta vãos inclinados (ha ≠ hb). "
        "Quando 'min_clearance_m' é fornecido, retorna 'within_clearance' "
        "indicando se a flecha respeita a distância mínima ao solo (NBR 5422: "
        "BT urbana=6,0 m, BT rural=5,5 m, MT=7,0 m)."
    ),
)
def calculate_catenary(request: CatenaryRequest) -> CatenaryResponse:
    """Calcula parâmetros da catenária e retorna flecha, constante e, opcionalmente, conformidade NBR 5422."""
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

    within_clearance: Optional[bool] = None
    if request.min_clearance_m is not None:
        domain_result = CatenaryResult(
            sag=float(result["sag"]),
            tension=float(result["tension"]),
            catenary_constant=float(result["catenary_constant"]),
        )
        within_clearance = _domain_service.is_within_clearance(domain_result, request.min_clearance_m)

    return CatenaryResponse(
        sag=float(result["sag"]),
        tension=float(result["tension"]),
        catenary_constant=float(result["catenary_constant"]),
        within_clearance=within_clearance,
    )
