"""
Rota de cálculo elétrico — API REST sisPROJETOS.

Endpoints:
- GET  /api/v1/electrical/standards     — Lista padrões normativos disponíveis (ABNT/ANEEL/PRODIST)
- GET  /api/v1/electrical/materials     — Lista materiais e resistividades do catálogo
- POST /api/v1/electrical/voltage-drop  — Cálculo de queda de tensão (NBR 5410 / ANEEL PRODIST)
- POST /api/v1/electrical/batch         — Cálculo em lote de queda de tensão (até 20 circuitos)
"""

from typing import List

from fastapi import APIRouter, HTTPException

from api.schemas import (
    MaterialOut,
    StandardOut,
    VoltageBatchRequest,
    VoltageBatchResponse,
    VoltageBatchResponseItem,
    VoltageDropRequest,
    VoltageDropResponse,
)
from domain.standards import ALL_STANDARDS, NBR_5410, get_standard_by_name
from modules.electrical.logic import ElectricalLogic
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/electrical", tags=["Elétrico"])
_logic = ElectricalLogic()


@router.get(
    "/standards",
    response_model=List[StandardOut],
    summary="Lista padrões normativos de queda de tensão",
    description=(
        "Retorna todos os padrões regulatórios disponíveis para avaliação de queda de tensão: "
        "ABNT NBR 5410, ANEEL/PRODIST Módulo 8 (BT e MT) e normas de concessionárias (Light, Enel). "
        "Use o campo 'name' para selecionar o padrão no campo 'standard_name' do endpoint /voltage-drop. "
        "Quando 'overrides_abnt=true', o campo 'override_toast_pt_br' deve ser exibido como toast na interface."
    ),
)
def list_standards() -> List[StandardOut]:
    """Retorna todos os padrões normativos pré-definidos ordenados por limite máximo."""
    return [
        StandardOut(
            name=s.name,
            source=s.source,
            max_drop_percent=s.max_drop_percent,
            overrides_abnt=s.overrides_abnt,
            override_toast_pt_br=s.override_toast_pt_br if s.override_toast_pt_br else None,
        )
        for s in sorted(ALL_STANDARDS, key=lambda s: s.max_drop_percent)
    ]


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
    summary="Calcula queda de tensão (NBR 5410 / ANEEL PRODIST)",
    description=(
        "Calcula a queda de tensão percentual em um circuito elétrico conforme o padrão normativo "
        "selecionado. Por padrão aplica NBR 5410 (limite 5%). Quando uma norma de concessionária ou "
        "ANEEL/PRODIST é selecionada via 'standard_name', a ABNT é ignorada e a resposta inclui "
        "'override_toast' com a mensagem de aviso em pt-BR a ser exibida na interface."
    ),
)
def calculate_voltage_drop(request: VoltageDropRequest) -> VoltageDropResponse:
    """Calcula queda de tensão e retorna resultado estruturado com padrão normativo aplicado."""
    # Resolve normative standard (default: NBR 5410)
    if request.standard_name is not None:
        standard = get_standard_by_name(request.standard_name)
        if standard is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Padrão normativo desconhecido: '{request.standard_name}'. "
                    "Use GET /api/v1/electrical/standards para listar os disponíveis."
                ),
            )
    else:
        standard = NBR_5410

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

    return VoltageDropResponse(
        current=result["current"],
        delta_v_volts=result["delta_v_volts"],
        percentage_drop=result["percentage_drop"],
        allowed=standard.check(result["percentage_drop"]),
        standard_name=standard.name,
        override_toast=standard.override_toast_pt_br if standard.override_toast_pt_br else None,
    )


@router.post(
    "/batch",
    response_model=VoltageBatchResponse,
    summary="Calcula queda de tensão em lote (múltiplos circuitos)",
    description=(
        "Processa até 20 circuitos elétricos em uma única chamada API, calculando queda de tensão "
        "para cada um. Cada circuito pode usar um padrão normativo diferente (NBR 5410, PRODIST BT/MT, "
        "Light ou Enel). Falhas individuais (dados inválidos ou material desconhecido) retornam "
        "'success=False' para o item sem abortar os demais circuitos do lote. "
        "Ideal para integração BIM com múltiplos ramais de uma rede de distribuição."
    ),
)
def calculate_voltage_drop_batch(request: VoltageBatchRequest) -> VoltageBatchResponse:
    """Calcula queda de tensão para múltiplos circuitos em lote (máximo 20)."""
    response_items: List[VoltageBatchResponseItem] = []

    for idx, item in enumerate(request.items):
        try:
            # Resolve normative standard per circuit (default: NBR 5410)
            if item.standard_name is not None:
                standard = get_standard_by_name(item.standard_name)
                if standard is None:
                    response_items.append(
                        VoltageBatchResponseItem(
                            index=idx,
                            label=item.label,
                            success=False,
                            error=(
                                f"Padrão normativo desconhecido: '{item.standard_name}'. "
                                "Use GET /api/v1/electrical/standards para listar os disponíveis."
                            ),
                        )
                    )
                    continue
            else:
                standard = NBR_5410

            result = _logic.calculate_voltage_drop(
                power_kw=item.power_kw,
                distance_m=item.distance_m,
                voltage_v=item.voltage_v,
                material=item.material,
                section_mm2=item.section_mm2,
                cos_phi=item.cos_phi,
                phases=item.phases,
            )
            if result is None:
                response_items.append(
                    VoltageBatchResponseItem(
                        index=idx,
                        label=item.label,
                        success=False,
                        error="Dados inválidos para o cálculo de queda de tensão.",
                    )
                )
                continue

            response_items.append(
                VoltageBatchResponseItem(
                    index=idx,
                    label=item.label,
                    success=True,
                    current=result["current"],
                    delta_v_volts=result["delta_v_volts"],
                    percentage_drop=result["percentage_drop"],
                    allowed=standard.check(result["percentage_drop"]),
                    standard_name=standard.name,
                    override_toast=standard.override_toast_pt_br if standard.override_toast_pt_br else None,
                )
            )
        except Exception as exc:
            logger.warning("Erro no item %d do lote elétrico: %s", idx, exc)
            response_items.append(
                VoltageBatchResponseItem(
                    index=idx,
                    label=item.label,
                    success=False,
                    error=str(exc),
                )
            )

    success_count = sum(1 for r in response_items if r.success)
    return VoltageBatchResponse(
        count=len(response_items),
        success_count=success_count,
        error_count=len(response_items) - success_count,
        items=response_items,
    )
