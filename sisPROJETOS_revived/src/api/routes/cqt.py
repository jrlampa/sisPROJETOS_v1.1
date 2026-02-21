"""
Rota de cálculo CQT — API REST sisPROJETOS.

Endpoint: POST /api/v1/cqt/calculate
Calcula queda de tensão de circuito (CQT) pela metodologia Enel.
"""

from fastapi import APIRouter
from api.schemas import CQTRequest, CQTResponse
from modules.cqt.logic import CQTLogic
from utils.logger import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/cqt", tags=["CQT"])
_logic = CQTLogic()


@router.post(
    "/calculate",
    response_model=CQTResponse,
    summary="Calcula CQT/BDI da rede (Metodologia Enel)",
    description=(
        "Executa o cálculo de Custo de Queda de Tensão (CQT) e "
        "Balanço de Demanda e Investimento (BDI) para uma rede de distribuição, "
        "conforme metodologia Enel (CNS-OMBR-MAT-19-0285)."
    ),
)
def calculate_cqt(request: CQTRequest) -> CQTResponse:
    """Calcula CQT por ordenação topológica dos trechos de rede."""
    segments = [seg.model_dump() for seg in request.segments]
    result = _logic.calculate(segments, request.trafo_kva, request.social_class)
    return CQTResponse(**result)
