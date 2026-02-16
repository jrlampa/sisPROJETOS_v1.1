import os
import shutil
import datetime
from utils.resource_manager import get_resource_manager

class ProjectCreatorLogic:
    def __init__(self):
        # Use the ResourceManager to find templates
        self.rm = get_resource_manager()
        self.templates_dir = self.rm.templates_dir

    def create_structure(self, project_name, base_path):
        """
        Creates a new project folder structure and copies templates.
        
        Args:
            project_name (str): The name of the project folder.
            base_path (str): The parent directory.
            
        Returns:
            tuple: (bool, str) - (Success Status, Message/Error)
        """
        try:
            full_path = os.path.join(base_path, project_name)
            
            if os.path.exists(full_path):
                return False, f"Erro: A pasta '{project_name}' já existe."
            
            # Create directories
            os.makedirs(full_path)
            os.makedirs(os.path.join(full_path, "1_Documentos"))
            os.makedirs(os.path.join(full_path, "2_Desenhos"))
            os.makedirs(os.path.join(full_path, "3_Calculos"))
            os.makedirs(os.path.join(full_path, "4_Fotos"))
            
            # Copy Templates
            # Prancha DWG -> 2_Desenhos
            prancha_src = os.path.join(self.templates_dir, "prancha.dwg")
            if os.path.exists(prancha_src):
                shutil.copy(prancha_src, os.path.join(full_path, "2_Desenhos", f"{project_name}_prancha.dwg"))
            
            # Excels -> 3_Calculos
            for xls in ["cqt.xlsx", "ambiental.xlsx"]:
                src = os.path.join(self.templates_dir, xls)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(full_path, "3_Calculos", xls))
            
            # Create Info file
            with open(os.path.join(full_path, "info.txt"), "w") as f:
                f.write(f"Projeto: {project_name}\n")
                f.write(f"Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                
            return True, "Sucesso"
        except Exception as e:
            return False, f"Erro ao criar projeto: {str(e)}"
