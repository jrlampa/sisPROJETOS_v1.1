"""
Rota de cálculo elétrico — API REST sisPROJETOS.

Endpoint: POST /api/v1/electrical/voltage-drop
Calcula queda de tensão conforme NBR 5410.
"""

from fastapi import APIRouter, HTTPException

from api.schemas import VoltageDropRequest, VoltageDropResponse
from modules.electrical.logic import ElectricalLogic
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/electrical", tags=["Elétrico"])
_logic = ElectricalLogic()


@router.post(
    "/voltage-drop",
    response_model=VoltageDropResponse,
    summary="Calcula queda de tensão (NBR 5410)",
    description=(
        "Calcula a queda de tensão percentual em um circuito elétrico "
        "com base na potência, distância, tensão, material e seção do condutor, "
        "conforme NBR 5410."
    ),
)
def calculate_voltage_drop(request: VoltageDropRequest) -> VoltageDropResponse:
    """Calcula queda de tensão e retorna resultado estruturado."""
    result = _logic.calculate_voltage_drop(
        power_kw=request.power_kw,
        distance_m=request.distance_m,
        voltage_v=request.voltage_v,
        material=request.material,
        section_mm2=request.section_mm2,
        cos_phi=request.cos_phi,
        phases=request.phases,
    )
    if result is None:
        logger.warning("Cálculo de queda de tensão retornou None para %s", request.model_dump())
        raise HTTPException(status_code=422, detail="Dados inválidos para o cálculo de queda de tensão.")
    return VoltageDropResponse(**result)
