"""
Rota de cálculo de esforços em postes — API REST sisPROJETOS.

Endpoints:
- POST /api/v1/pole-load/resultant  — Calcula resultante de esforços em poste
- POST /api/v1/pole-load/report     — Gera relatório PDF em Base64 (NBR 8451/8452)
- POST /api/v1/pole-load/batch      — Calcula esforços em lote (até 20 postes)
- GET  /api/v1/pole-load/suggest    — Sugere postes por força resultante (sem cálculo)
"""

import base64
from typing import List

from fastapi import APIRouter, HTTPException, Query

from api.schemas import (
    PoleLoadBatchRequest,
    PoleLoadBatchResponse,
    PoleLoadBatchResponseItem,
    PoleLoadReportRequest,
    PoleLoadReportResponse,
    PoleLoadRequest,
    PoleLoadResponse,
    PoleSuggestResponse,
)
from modules.pole_load.logic import PoleLoadLogic
from modules.pole_load.report import generate_report_to_buffer
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


@router.post(
    "/report",
    response_model=PoleLoadReportResponse,
    summary="Gera relatório PDF de esforços em postes (Base64)",
    description=(
        "Calcula a resultante de esforços e gera um relatório PDF completo em memória, "
        "retornando-o codificado em Base64 (RFC 4648). "
        "Inclui tabela de condutores com tração calculada e resultante vetorial, "
        "conforme NBR 8451/8452. Padrão consistente com POST /catenary/dxf."
    ),
)
def generate_pole_load_report(request: PoleLoadReportRequest) -> PoleLoadReportResponse:
    """Calcula a resultante e gera o relatório PDF em memória."""
    try:
        result = _logic.calculate_resultant(
            concessionaria=request.concessionaria,
            condicao=request.condicao,
            cabos_input=[c.model_dump() for c in request.cabos],
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Build cable data list for the report; 'rede' (network label) is set to the
    # conductor name since the GUI's network selector is not available in the API context.
    data = [{"rede": c.condutor, "condutor": c.condutor, "vao": c.vao, "angulo": c.angulo} for c in request.cabos]

    try:
        pdf_bytes = generate_report_to_buffer(data, result, request.project_name)
    except Exception as exc:
        logger.error("Erro ao gerar relatório PDF: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao gerar relatório PDF.") from exc

    filename = request.filename if request.filename.endswith(".pdf") else f"{request.filename}.pdf"
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    logger.debug("Relatório PDF gerado: %s (%d bytes)", filename, len(pdf_bytes))
    return PoleLoadReportResponse(
        pdf_base64=pdf_b64,
        filename=filename,
        resultant_force=result["resultant_force"],
    )


@router.post(
    "/batch",
    response_model=PoleLoadBatchResponse,
    summary="Calcula esforços em lote (múltiplos postes)",
    description=(
        "Processa até 20 postes em uma única chamada API, calculando a resultante de esforços "
        "para cada um conforme metodologias Light (flecha) e Enel (tabela). "
        "Falhas individuais (concessionária inválida, dados ausentes) retornam 'success=False' "
        "para o item sem abortar os demais postes do lote. "
        "Ideal para integração BIM com múltiplos postes de uma rede de distribuição."
    ),
)
def calculate_pole_load_batch(request: PoleLoadBatchRequest) -> PoleLoadBatchResponse:
    """Calcula resultante de esforços para múltiplos postes em lote (máximo 20)."""
    response_items: List[PoleLoadBatchResponseItem] = []

    for idx, item in enumerate(request.items):
        try:
            result = _logic.calculate_resultant(
                concessionaria=item.concessionaria,
                condicao=item.condicao,
                cabos_input=[c.model_dump() for c in item.cabos],
            )
            suggested = _logic.suggest_pole(result["resultant_force"])
            response_items.append(
                PoleLoadBatchResponseItem(
                    index=idx,
                    label=item.label,
                    success=True,
                    resultant_force=result["resultant_force"],
                    resultant_angle=result["resultant_angle"],
                    suggested_poles=suggested,
                )
            )
        except KeyError as exc:
            response_items.append(
                PoleLoadBatchResponseItem(
                    index=idx,
                    label=item.label,
                    success=False,
                    error=str(exc),
                )
            )
        except Exception as exc:
            logger.warning("Erro no item %d do lote de postes: %s", idx, exc)
            response_items.append(
                PoleLoadBatchResponseItem(
                    index=idx,
                    label=item.label,
                    success=False,
                    error=str(exc),
                )
            )

    success_count = sum(1 for r in response_items if r.success)
    return PoleLoadBatchResponse(
        count=len(response_items),
        success_count=success_count,
        error_count=len(response_items) - success_count,
        items=response_items,
    )
