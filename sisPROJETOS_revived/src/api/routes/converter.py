"""
Rota de conversão KML/KMZ — API REST sisPROJETOS.

Endpoints:
- POST /api/v1/converter/kml-to-utm  — Converte KML Base64 para coordenadas UTM JSON
- POST /api/v1/converter/utm-to-dxf  — Converte pontos UTM JSON para DXF Base64 (BIM)

Fluxo BIM completo (dois passos):
    KML Base64 → /kml-to-utm → pontos UTM JSON → /utm-to-dxf → DXF Base64
"""

import base64
from typing import List

import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas import KmlConvertRequest, KmlConvertResponse, KmlPointOut, UTMToDxfRequest, UTMToDxfResponse
from modules.converter.logic import ConverterLogic
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/converter", tags=["Conversor KML/KMZ"])
_logic = ConverterLogic()


@router.post(
    "/kml-to-utm",
    response_model=KmlConvertResponse,
    summary="Converte KML/KMZ para coordenadas UTM",
    description=(
        "Recebe o conteúdo de um arquivo KML ou KML interno de um KMZ codificado "
        "em Base64 (RFC 4648) e retorna a lista de placemarks com coordenadas UTM. "
        "A zona UTM é detectada automaticamente a partir da longitude de cada ponto. "
        "Compatível com Google Earth, QGIS e sistemas BIM. Zero custo — sem APIs externas."
    ),
)
def convert_kml_to_utm(request: KmlConvertRequest) -> KmlConvertResponse:
    """Decodifica KML Base64, extrai placemarks e converte para UTM."""
    # Decode Base64 payload
    try:
        content = base64.b64decode(request.kml_base64, validate=True)
    except Exception as exc:
        logger.warning("Payload Base64 inválido: %s", exc)
        raise HTTPException(
            status_code=422, detail="Conteúdo Base64 inválido. Verifique a codificação do arquivo KML."
        ) from exc

    # Extract placemarks from raw KML bytes
    try:
        placemarks = _logic.load_kml_content(content)
    except ValueError as exc:
        logger.warning("Falha ao carregar KML: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Convert to UTM
    try:
        df = _logic.convert_to_utm(placemarks)
    except ValueError as exc:
        logger.warning("Falha ao converter para UTM: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Build response
    points: List[KmlPointOut] = [
        KmlPointOut(
            name=str(row["Name"]),
            description=str(row.get("Description", "") or ""),
            type=str(row.get("Type", "Unknown")),
            longitude=float(row["Longitude"]),
            latitude=float(row["Latitude"]),
            easting=float(row["Easting"]),
            northing=float(row["Northing"]),
            zone=int(row["Zone"]),
            hemisphere=str(row["Hemisphere"]),
            elevation=float(row.get("Elevation", 0.0)),
        )
        for _, row in df.iterrows()
    ]

    return KmlConvertResponse(count=len(points), points=points)


@router.post(
    "/utm-to-dxf",
    response_model=UTMToDxfResponse,
    summary="Converte pontos UTM para DXF (Base64)",
    description=(
        "Recebe uma lista de pontos com coordenadas UTM (Easting, Northing, Elevation) "
        "e gera um arquivo DXF em memória, retornando-o codificado em Base64 (RFC 4648). "
        "Completa o pipeline BIM: KML → /kml-to-utm → /utm-to-dxf → DXF. "
        "Pontos únicos viram entidades POINT; múltiplos pontos com mesmo nome viram POLYLINE3D. "
        "DXF 2.5D — altitude em Z (NBR 13133). Zero custo — sem APIs externas."
    ),
)
def convert_utm_to_dxf(request: UTMToDxfRequest) -> UTMToDxfResponse:
    """Converte lista de pontos UTM em DXF e retorna como Base64."""
    # Build DataFrame from request points
    df = pd.DataFrame(
        [
            {"Name": p.name, "Easting": p.easting, "Northing": p.northing, "Elevation": p.elevation}
            for p in request.points
        ]
    )

    try:
        dxf_bytes = _logic.save_to_dxf_to_buffer(df)
    except ValueError as exc:
        logger.warning("Falha ao gerar DXF: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = request.filename if request.filename.endswith(".dxf") else f"{request.filename}.dxf"
    dxf_b64 = base64.b64encode(dxf_bytes).decode("utf-8")
    logger.debug("DXF UTM gerado: %s (%d bytes)", filename, len(dxf_bytes))
    return UTMToDxfResponse(dxf_base64=dxf_b64, filename=filename, count=len(request.points))
