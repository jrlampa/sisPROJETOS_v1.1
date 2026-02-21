"""
Fábrica da aplicação FastAPI — sisPROJETOS REST API.

Ponto de entrada para o servidor REST utilizado na integração
Half-way BIM e outras ferramentas externas.

Uso (desenvolvimento):
    cd sisPROJETOS_revived
    uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

Documentação interativa disponível em:
    http://localhost:8000/docs  (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

import os
import sys

# Garante que src/ esteja no path para importações dos módulos
_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)  # pragma: no cover

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from __version__ import __version__  # noqa: E402
from api.routes import catenary, converter, cqt, data, electrical, pole_load, project_creator


def create_app() -> FastAPI:
    """Cria e configura a instância FastAPI.

    Returns:
        FastAPI: Aplicação configurada com rotas, middlewares e metadados.
    """
    app = FastAPI(
        title="sisPROJETOS API",
        version=__version__,
        summary="API REST para integração Half-way BIM do sisPROJETOS",
        description=(
            "Fornece endpoints de cálculo de engenharia elétrica para integração "
            "com sistemas BIM (Building Information Modeling) e outras ferramentas. "
            "Cálculos seguem ABNT (NBR 5410, NBR 5422, NBR 8451) por padrão, com suporte "
            "a ANEEL/PRODIST Módulo 8 e normas de concessionárias (Light, Enel) via 'standard_name'."
        ),
        contact={"name": "sisPROJETOS", "url": "https://github.com/jrlampa/sisPROJETOS_v1.1"},
        license_info={"name": "MIT"},
        openapi_tags=[
            {"name": "Elétrico", "description": "Cálculos elétricos (NBR 5410)"},
            {"name": "CQT", "description": "Custo de Queda de Tensão — Metodologia Enel"},
            {"name": "Catenária", "description": "Cálculo de catenária de condutores e geração de DXF (NBR 5422)"},
            {"name": "Esforços em Postes", "description": "Esforços mecânicos em postes (NBR 8451)"},
            {"name": "Dados Mestres", "description": "Catálogos técnicos para integração BIM"},
            {"name": "Conversor KML/KMZ", "description": "Conversão KML/KMZ → UTM para integração geoespacial BIM"},
            {"name": "Projetos", "description": "Gestão de estrutura de pastas de projetos"},
        ],
    )

    # CORS — origens configuráveis via variável de ambiente CORS_ORIGINS.
    # Padrão "*" permite integração com qualquer ferramenta BIM (zero custo).
    # Em produção, defina CORS_ORIGINS="https://bim.exemplo.com.br" para restringir.
    cors_origins_env = os.getenv("CORS_ORIGINS", "*")
    cors_origins = [o.strip() for o in cors_origins_env.split(",")] if cors_origins_env != "*" else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Registro de rotas versionadas
    PREFIX = "/api/v1"
    app.include_router(electrical.router, prefix=PREFIX)
    app.include_router(cqt.router, prefix=PREFIX)
    app.include_router(catenary.router, prefix=PREFIX)
    app.include_router(pole_load.router, prefix=PREFIX)
    app.include_router(data.router, prefix=PREFIX)
    app.include_router(converter.router, prefix=PREFIX)
    app.include_router(project_creator.router, prefix=PREFIX)

    @app.get("/health", tags=["Infra"], summary="Verificação de saúde da API")
    def health_check():
        """Retorna status da API e versão da aplicação."""
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
