"""
Rota de criação de estrutura de projeto — API REST sisPROJETOS.

Endpoint: POST /api/v1/projects/create
Cria a estrutura de pastas padronizada para um novo projeto de distribuição,
copiando os templates necessários (prancha DWG, planilhas CQT e Ambiental).
"""

from pathlib import Path

from fastapi import APIRouter

from api.schemas import ProjectCreateRequest, ProjectCreateResponse
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
