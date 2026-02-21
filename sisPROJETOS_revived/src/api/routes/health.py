"""
Rota de verificação de saúde da API — sisPROJETOS REST API.

Endpoint:
- GET /health  — Verificação de saúde (status, versão, DB, ambiente, timestamp)

Utilizado pelo Docker HEALTHCHECK e sistemas de monitoramento enterprise.
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter

from __version__ import __version__
from api.schemas import HealthResponse
from database.db_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Infra"])

_db = DatabaseManager()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verificação de saúde da API",
    description=(
        "Retorna status operacional da API, conectividade com o banco de dados, "
        "versão da aplicação, ambiente de execução e timestamp UTC. "
        "Utilizado pelo Docker HEALTHCHECK e ferramentas de monitoramento enterprise. "
        "Retorna HTTP 200 com status='ok' quando todos os subsistemas estão operacionais, "
        "ou status='degraded' quando o DB está inacessível (API continua respondendo)."
    ),
)
def health_check() -> HealthResponse:
    """Verifica e retorna o estado de saúde de todos os subsistemas.

    Returns:
        HealthResponse: Estado da API com status, versão, DB, ambiente e timestamp.
    """
    # Verifica conectividade com o banco de dados
    db_status = "ok"
    try:
        conductors = _db.get_all_conductors()
        logger.debug("DB health check: %d condutores encontrados.", len(conductors))
    except Exception as exc:
        db_status = "error"
        logger.warning("DB health check falhou: %s", exc)

    overall_status = "ok" if db_status == "ok" else "degraded"

    environment = "development" if os.getenv("DEBUG", "False").lower() == "true" else "production"

    return HealthResponse(
        status=overall_status,
        version=__version__,
        db_status=db_status,
        environment=environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
