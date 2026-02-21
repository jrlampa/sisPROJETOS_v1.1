"""
Rota de cálculo de catenária — API REST sisPROJETOS.

Endpoints:
- POST /api/v1/catenary/calculate   Calcula flecha e constante catenária (NBR 5422).
- POST /api/v1/catenary/dxf         Gera arquivo DXF da curva catenária (retorna Base64).
"""

import base64
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from api.schemas import CatenaryDxfRequest, CatenaryDxfResponse, CatenaryRequest, CatenaryResponse
from domain.services import CatenaryDomainService
from domain.value_objects import CatenaryResult
from modules.catenaria.logic import CatenaryLogic
from utils.dxf_manager import DXFManager
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
        "BT urbana=6,0 m, BT rural=5,5 m, MT=7,0 m). "
        "Quando 'include_curve=true', retorna os 100 pontos (X,Y) da curva para "
        "renderização em ferramentas BIM e CAD externas."
    ),
)
def calculate_catenary(request: CatenaryRequest) -> CatenaryResponse:
    """Calcula parâmetros da catenária e retorna flecha, constante, conformidade NBR 5422 e pontos de curva."""
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

    curve_x: Optional[List[float]] = None
    curve_y: Optional[List[float]] = None
    if request.include_curve:
        curve_x = [float(v) for v in result["x_vals"]]
        curve_y = [float(v) for v in result["y_vals"]]

    return CatenaryResponse(
        sag=float(result["sag"]),
        tension=float(result["tension"]),
        catenary_constant=float(result["catenary_constant"]),
        within_clearance=within_clearance,
        curve_x=curve_x,
        curve_y=curve_y,
    )


@router.post(
    "/dxf",
    response_model=CatenaryDxfResponse,
    summary="Gera DXF da catenária via API (NBR 5422 / BIM)",
    description=(
        "Calcula a curva catenária e retorna um arquivo DXF profissional codificado em Base64 "
        "para integração com ferramentas BIM e CAD. "
        "O DXF segue a convenção 2.5D com layers: CATENARY_CURVE (verde), "
        "SUPPORTS (amarelo) e ANNOTATIONS (branco/preto). "
        "Compatível com AutoCAD, QGIS, Civil 3D e outros viewers CAD."
    ),
)
def generate_catenary_dxf(request: CatenaryDxfRequest) -> CatenaryDxfResponse:
    """Gera DXF da catenária em memória e retorna como Base64 para download via API."""
    result = _logic.calculate_catenary(
        span=request.span,
        ha=request.ha,
        hb=request.hb,
        tension_daN=request.tension_daN,
        weight_kg_m=request.weight_kg_m,
    )
    if result is None:
        logger.warning("Cálculo de catenária retornou None para DXF: %s", request.model_dump())
        raise HTTPException(status_code=422, detail="Peso linear zero ou dados inválidos para o cálculo.")

    safe_filename = request.filename if request.filename.endswith(".dxf") else f"{request.filename}.dxf"

    dxf_bytes = DXFManager.create_catenary_dxf_to_buffer(
        x_vals=result["x_vals"],
        y_vals=result["y_vals"],
        sag=float(result["sag"]),
    )

    return CatenaryDxfResponse(
        dxf_base64=base64.b64encode(dxf_bytes).decode("ascii"),
        filename=safe_filename,
        sag=float(result["sag"]),
        catenary_constant=float(result["catenary_constant"]),
    )
