"""
Rota de cálculo elétrico — API REST sisPROJETOS.

Endpoints:
- POST /api/v1/electrical/voltage-drop  — Cálculo de queda de tensão (NBR 5410)
- GET  /api/v1/electrical/materials     — Lista materiais e resistividades do catálogo
"""

from typing import List

from fastapi import APIRouter, HTTPException

from api.schemas import MaterialOut, VoltageDropRequest, VoltageDropResponse
from modules.electrical.logic import ElectricalLogic
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/electrical", tags=["Elétrico"])
_logic = ElectricalLogic()


@router.get(
    "/materials",
    response_model=List[MaterialOut],
    summary="Lista materiais condutores disponíveis",
    description=(
        "Retorna os materiais condutores cadastrados no banco de dados com suas "
        "resistividades (Ω·mm²/m a 20°C), conforme NBR 5410. "
        "Use para descobrir os valores válidos do campo 'material' antes de chamar /voltage-drop."
    ),
)
def list_materials() -> List[MaterialOut]:
    """Retorna todos os materiais com resistividade do catálogo técnico."""
    try:
        rows = _logic.get_materials()
    except Exception as exc:
        logger.error("Erro ao consultar materiais: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao consultar catálogo de materiais.") from exc
    return [MaterialOut(**r) for r in rows]


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
