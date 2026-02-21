"""
Rota de gestão de projetos — API REST sisPROJETOS.

Endpoints:
- POST /api/v1/projects/create — Cria estrutura de pastas padronizada
- GET  /api/v1/projects/list   — Lista projetos em um diretório base
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from api.schemas import ProjectCreateRequest, ProjectCreateResponse, ProjectListResponse
from modules.project_creator.logic import ProjectCreatorLogic
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/projects", tags=["Projetos"])
_logic = ProjectCreatorLogic()


@router.post(
    "/create",
    response_model=ProjectCreateResponse,
    summary="Cria estrutura de pastas de projeto",
    description=(
        "Cria a estrutura de pastas padronizada para um novo projeto de distribuição elétrica, "
        "copiando os templates necessários (prancha DWG, planilhas CQT e Ambiental). "
        "Segue a estrutura: {project_name}/1_Documentos, 2_Desenhos, 3_Calculos, 4_Fotos."
    ),
)
def create_project(request: ProjectCreateRequest) -> ProjectCreateResponse:
    """Cria a estrutura de pastas do projeto e copia os templates."""
    logger.info("API: criando projeto '%s' em '%s'", request.project_name, request.base_path)
    success, message = _logic.create_structure(request.project_name, request.base_path)

    project_path = str(Path(request.base_path) / request.project_name) if success else None
    return ProjectCreateResponse(success=success, message=message, project_path=project_path)


@router.get(
    "/list",
    response_model=ProjectListResponse,
    summary="Lista projetos em um diretório base",
    description=(
        "Retorna a lista de diretórios de projetos existentes em um diretório base informado. "
        "Útil para integração BIM: descobrir projetos criados antes de acessar seus dados. "
        "Retorna lista vazia se o diretório existir mas não contiver subpastas."
    ),
)
def list_projects(
    base_path: str = Query(..., description="Caminho absoluto do diretório base a pesquisar"),
) -> ProjectListResponse:
    """Lista subdiretórios de projetos criados em base_path."""
    logger.debug("API: listando projetos em '%s'", base_path)

    # Path traversal protection: reject null bytes and non-absolute paths
    if "\x00" in base_path:
        raise HTTPException(status_code=422, detail="Caminho inválido: contém caracteres nulos.")

    resolved = Path(base_path).resolve()
    if not resolved.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"Diretório base não encontrado: {base_path}",
        )

    try:
        project_names = sorted(
            entry.name for entry in resolved.iterdir() if entry.is_dir() and not entry.name.startswith(".")
        )
    except PermissionError as exc:
        logger.error("Sem permissão para listar '%s': %s", base_path, exc)
        raise HTTPException(status_code=403, detail="Sem permissão para acessar o diretório.") from exc
    except OSError as exc:
        logger.error("Erro ao listar projetos em '%s': %s", base_path, exc)
        raise HTTPException(status_code=500, detail="Erro ao listar projetos.") from exc

    logger.info("API: %d projeto(s) encontrado(s) em '%s'", len(project_names), base_path)
    return ProjectListResponse(base_path=str(resolved), projects=project_names, count=len(project_names))
