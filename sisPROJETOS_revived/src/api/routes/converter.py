"""
Rota de conversão KML/KMZ → UTM — API REST sisPROJETOS.

Endpoint: POST /api/v1/converter/kml-to-utm
Converte conteúdo KML (codificado em Base64) para coordenadas UTM,
permitindo integração direta com ferramentas BIM sem acesso ao disco local.

Fluxo:
    1. Cliente envia KML em Base64 no corpo JSON
    2. API decodifica e passa os bytes para ConverterLogic.load_kml_content()
    3. ConverterLogic.convert_to_utm() projeta para UTM via pyproj
    4. Retorna lista estruturada de pontos UTM em JSON
"""

import base64
from typing import List

from fastapi import APIRouter, HTTPException

from api.schemas import KmlConvertRequest, KmlConvertResponse, KmlPointOut
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
