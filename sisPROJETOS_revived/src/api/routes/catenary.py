"""
Rota de cálculo de catenária — API REST sisPROJETOS.

Endpoints:
- POST /api/v1/catenary/calculate   Calcula flecha e constante catenária (NBR 5422).
- POST /api/v1/catenary/dxf         Gera arquivo DXF da curva catenária (retorna Base64).
- POST /api/v1/catenary/batch       Calcula múltiplos vãos em lote (BIM efficiency).
- GET  /api/v1/catenary/clearances  Tabela de folgas mínimas NBR 5422 / PRODIST Módulo 6.
"""

import base64
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from api.schemas import (
    CatenaryBatchRequest,
    CatenaryBatchResponse,
    CatenaryBatchResponseItem,
    CatenaryDxfRequest,
    CatenaryDxfResponse,
    CatenaryRequest,
    CatenaryResponse,
    ClearancesResponse,
    ClearanceTypeOut,
)
from domain.services import CatenaryDomainService
from domain.value_objects import CatenaryResult
from modules.catenaria.logic import CatenaryLogic
from utils.dxf_manager import DXFManager
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/catenary", tags=["Catenária"])
_logic = CatenaryLogic()
_domain_service = CatenaryDomainService()

# ── Tabela de folgas mínimas NBR 5422 / PRODIST Módulo 6 ─────────────────────
# Valores de referência para o campo min_clearance_m do endpoint /calculate.
# Hierarquia: norma da concessionária > ANEEL/PRODIST > ABNT.
_CLEARANCES: List[ClearanceTypeOut] = [
    ClearanceTypeOut(
        network_type="BT_URBANA",
        description="Baixa Tensão — Área Urbana (≤ 1 kV)",
        min_clearance_m=6.0,
        standard_ref="NBR 5422 Tabela 6 / PRODIST Módulo 6",
    ),
    ClearanceTypeOut(
        network_type="BT_RURAL",
        description="Baixa Tensão — Área Rural (≤ 1 kV)",
        min_clearance_m=5.5,
        standard_ref="NBR 5422 Tabela 6 / PRODIST Módulo 6",
    ),
    ClearanceTypeOut(
        network_type="MT_URBANA",
        description="Média Tensão — Área Urbana (1–36 kV)",
        min_clearance_m=7.0,
        standard_ref="NBR 5422 Tabela 6 / PRODIST Módulo 6 / Light e Enel",
    ),
    ClearanceTypeOut(
        network_type="MT_RURAL",
        description="Média Tensão — Área Rural (1–36 kV)",
        min_clearance_m=7.0,
        standard_ref="NBR 5422 Tabela 6 / PRODIST Módulo 6",
    ),
    ClearanceTypeOut(
        network_type="AT_69KV",
        description="Alta Tensão — 69 kV",
        min_clearance_m=8.5,
        standard_ref="NBR 5422 Tabela 6",
    ),
    ClearanceTypeOut(
        network_type="AT_138KV",
        description="Alta Tensão — 138 kV",
        min_clearance_m=9.5,
        standard_ref="NBR 5422 Tabela 6",
    ),
    ClearanceTypeOut(
        network_type="AT_230KV",
        description="Alta Tensão — 230 kV",
        min_clearance_m=10.5,
        standard_ref="NBR 5422 Tabela 6",
    ),
]


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


@router.get(
    "/clearances",
    response_model=ClearancesResponse,
    summary="Tabela de folgas mínimas ao solo por tipo de rede (NBR 5422 / PRODIST Módulo 6)",
    description=(
        "Retorna a tabela de distâncias mínimas de segurança ao solo para cada tipo de rede elétrica "
        "conforme NBR 5422 Tabela 6 e PRODIST Módulo 6. "
        "Use o valor de 'min_clearance_m' do tipo de rede correspondente como parâmetro "
        "'min_clearance_m' no endpoint POST /api/v1/catenary/calculate para verificar conformidade NBR 5422. "
        "Quando a concessionária possuir norma própria, seu valor prevalece sobre a ABNT (exibir toast)."
    ),
)
def get_clearances() -> ClearancesResponse:
    """Retorna tabela de folgas mínimas ao solo por tipo de rede (NBR 5422 / PRODIST Módulo 6)."""
    return ClearancesResponse(
        clearances=_CLEARANCES,
        count=len(_CLEARANCES),
    )


@router.post(
    "/batch",
    response_model=CatenaryBatchResponse,
    summary="Cálculo de catenária em lote (múltiplos vãos — BIM)",
    description=(
        "Calcula flecha, tensão e constante catenária para até 20 vãos em uma única chamada, "
        "evitando N chamadas individuais ao endpoint /calculate. "
        "Ideal para integração BIM com linhas de distribuição com múltiplos vãos. "
        "Vãos com parâmetros inválidos retornam 'success=false' com descrição do erro, "
        "sem abortar o processamento dos demais itens."
    ),
)
def calculate_catenary_batch(request: CatenaryBatchRequest) -> CatenaryBatchResponse:
    """Processa múltiplos vãos de catenária em lote; erros individuais não abortam o lote."""
    response_items: List[CatenaryBatchResponseItem] = []

    for idx, item in enumerate(request.items):
        try:
            result = _logic.calculate_catenary(
                span=item.span,
                ha=item.ha,
                hb=item.hb,
                tension_daN=item.tension_daN,
                weight_kg_m=item.weight_kg_m,
            )
            if result is None:
                response_items.append(
                    CatenaryBatchResponseItem(
                        index=idx,
                        label=item.label,
                        success=False,
                        error="Peso linear zero ou dados inválidos para o cálculo.",
                    )
                )
                continue

            within_clearance: Optional[bool] = None
            if item.min_clearance_m is not None:
                domain_result = CatenaryResult(
                    sag=float(result["sag"]),
                    tension=float(result["tension"]),
                    catenary_constant=float(result["catenary_constant"]),
                )
                within_clearance = _domain_service.is_within_clearance(domain_result, item.min_clearance_m)

            response_items.append(
                CatenaryBatchResponseItem(
                    index=idx,
                    label=item.label,
                    success=True,
                    sag=float(result["sag"]),
                    tension=float(result["tension"]),
                    catenary_constant=float(result["catenary_constant"]),
                    within_clearance=within_clearance,
                )
            )
        except Exception as exc:
            logger.warning("Erro no item %d do lote de catenária: %s", idx, exc)
            response_items.append(
                CatenaryBatchResponseItem(
                    index=idx,
                    label=item.label,
                    success=False,
                    error=str(exc),
                )
            )

    success_count = sum(1 for r in response_items if r.success)
    return CatenaryBatchResponse(
        count=len(response_items),
        success_count=success_count,
        error_count=len(response_items) - success_count,
        items=response_items,
    )
