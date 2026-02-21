import shutil
import datetime
from pathlib import Path
from utils.resource_manager import get_resource_manager
from utils.logger import get_logger
from utils.sanitizer import sanitize_string, sanitize_filepath

# Configure logging
logger = get_logger(__name__)


class ProjectCreatorLogic:
    def __init__(self):
        """Initialize ProjectCreatorLogic with resource manager."""
        # Use the ResourceManager to find templates
        self.rm = get_resource_manager()
        self.templates_dir = Path(self.rm.templates_dir)

    def _validate_templates_directory(self):
        """Validate that templates directory exists.

        Returns:
            bool: True if directory exists, False otherwise
        """
        if not self.templates_dir.exists():
            logger.error(f"Templates directory not found: {self.templates_dir}")
            return False

        if not self.templates_dir.is_dir():
            logger.error(f"Templates path is not a directory: {self.templates_dir}")
            return False

        return True

    def create_structure(self, project_name, base_path):
        """
        Creates a new project folder structure and copies templates.

        Folder Structure:
            {project_name}/
                1_Documentos/
                2_Desenhos/
                    {project_name}_prancha.dwg
                3_Calculos/
                    {project_name}_CQT.xlsx
                    {project_name}_Ambiental.xlsx
                4_Fotos/
                info.txt

        Args:
            project_name (str): The name of the project folder.
            base_path (str): The parent directory.

        Returns:
            tuple: (bool, str) - (Success Status, Message/Error)
        """
        try:
            project_name = sanitize_string(project_name, max_length=100, allow_empty=False)
            base_path_str = sanitize_filepath(str(base_path))
        except ValueError as e:
            logger.warning("Entrada inválida em create_structure: %s", e)
            return False, f"Erro: {e}"

        try:
            # Validate templates directory
            if not self._validate_templates_directory():
                return False, "Erro: Diretório de templates não encontrado. Reinstale o aplicativo."

            # Convert to Path objects for better handling
            base_path = Path(base_path_str)
            full_path = base_path / project_name

            # Check if project already exists
            if full_path.exists():
                return False, f"Erro: A pasta '{project_name}' já existe."

            # Create main project directory
            full_path.mkdir(parents=True, exist_ok=False)

            # Create subdirectories
            folders = ["1_Documentos", "2_Desenhos", "3_Calculos", "4_Fotos"]

            for folder in folders:
                (full_path / folder).mkdir(exist_ok=True)

            # Copy and rename templates
            templates_copied = 0
            templates_missing = []

            # Template mapping: (source_name, destination_folder, renamed_pattern)
            template_mappings = [
                ("prancha.dwg", "2_Desenhos", f"{project_name}_prancha.dwg"),
                ("cqt.xlsx", "3_Calculos", f"{project_name}_CQT.xlsx"),
                ("ambiental.xlsx", "3_Calculos", f"{project_name}_Ambiental.xlsx"),
            ]

            for source_name, dest_folder, new_name in template_mappings:
                source_path = self.templates_dir / source_name
                dest_path = full_path / dest_folder / new_name

                if source_path.exists():
                    try:
                        shutil.copy2(source_path, dest_path)
                        templates_copied += 1
                        logger.info(f"Template copied: {source_name} -> {new_name}")
                    except Exception as copy_error:
                        logger.warning(f"Failed to copy {source_name}: {copy_error}")
                        templates_missing.append(source_name)
                else:
                    logger.warning(f"Template not found: {source_name}")
                    templates_missing.append(source_name)

            # Create project info file
            info_path = full_path / "info.txt"
            with info_path.open("w", encoding="utf-8") as f:
                f.write(f"Projeto: {project_name}\n")
                f.write(f"Data de Criação: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write(f"Templates Copiados: {templates_copied}/{len(template_mappings)}\n")
                if templates_missing:
                    f.write(f"Templates Ausentes: {', '.join(templates_missing)}\n")

            # Build success message
            if templates_missing:
                warning_msg = f"\n⚠️ Alguns templates não foram encontrados: {', '.join(templates_missing)}"
                return True, f"Projeto criado com sucesso!{warning_msg}"

            return True, "Projeto criado com sucesso!"

        except PermissionError:
            return False, f"Erro: Sem permissão para criar pasta em '{base_path}'."
        except OSError as os_error:
            return False, f"Erro do sistema ao criar projeto: {str(os_error)}"
        except Exception as e:
            logger.exception("Unexpected error creating project")
            return False, f"Erro inesperado ao criar projeto: {str(e)}"
