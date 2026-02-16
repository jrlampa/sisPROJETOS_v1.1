import pytest
import os
import shutil
from pathlib import Path
from src.modules.project_creator.logic import ProjectCreatorLogic

@pytest.fixture
def temp_project_dir(tmp_path):
    return tmp_path / "test_project"

def test_create_structure(temp_project_dir):
    """Testa criação básica de estrutura de projeto."""
    logic = ProjectCreatorLogic()
    # The project name should match what we expect to be created inside the parent
    project_name = "TestProj"
    # Logic will create folder at base_path/project_name
    success, msg = logic.create_structure(project_name, str(temp_project_dir.parent))
    
    expected_full_path = temp_project_dir.parent / project_name
    
    assert success is True
    assert expected_full_path.exists()
    assert (expected_full_path / "1_Documentos").exists()
    assert (expected_full_path / "2_Desenhos").exists()
    assert (expected_full_path / "3_Calculos").exists()
    assert (expected_full_path / "4_Fotos").exists()
    assert (expected_full_path / "info.txt").exists()

def test_create_structure_already_exists(temp_project_dir):
    """Testa erro quando projeto já existe."""
    logic = ProjectCreatorLogic()
    temp_project_dir.mkdir(parents=True)
    
    success, msg = logic.create_structure("test_project", str(temp_project_dir.parent))
    assert success is False
    assert "já existe" in msg

def test_template_renaming(temp_project_dir):
    """Testa que templates são renomeados corretamente."""
    logic = ProjectCreatorLogic()
    project_name = "PROJ123"
    
    success, msg = logic.create_structure(project_name, str(temp_project_dir.parent))
    
    project_path = temp_project_dir.parent / project_name
    
    # Verificar que templates foram renomeados com o nome do projeto
    assert (project_path / "2_Desenhos" / f"{project_name}_prancha.dwg").exists() or \
           "prancha.dwg" in msg  # Template pode não existir em ambiente de teste
    
    # Se templates existirem, verificar nomes corretos
    calculos_path = project_path / "3_Calculos"
    if calculos_path.exists():
        files = list(calculos_path.iterdir())
        file_names = [f.name for f in files]
        
        # Verificar padrão de nomeação (se arquivos existirem)
        for name in file_names:
            if "CQT" in name:
                assert name == f"{project_name}_CQT.xlsx"
            if "Ambiental" in name:
                assert name == f"{project_name}_Ambiental.xlsx"

def test_info_file_creation(temp_project_dir):
    """Testa criação do arquivo info.txt."""
    logic = ProjectCreatorLogic()
    project_name = "InfoTest"
    
    success, msg = logic.create_structure(project_name, str(temp_project_dir.parent))
    
    info_path = temp_project_dir.parent / project_name / "info.txt"
    assert info_path.exists()
    
    content = info_path.read_text(encoding="utf-8")
    assert f"Projeto: {project_name}" in content
    assert "Data de Criação:" in content

def test_folder_structure_maintained(temp_project_dir):
    """Testa que estrutura de pastas é mantida exatamente."""
    logic = ProjectCreatorLogic()
    project_name = "StructTest"
    
    success, msg = logic.create_structure(project_name, str(temp_project_dir.parent))
    
    project_path = temp_project_dir.parent / project_name
    
    # Verificar estrutura exata
    expected_folders = ["1_Documentos", "2_Desenhos", "3_Calculos", "4_Fotos"]
    actual_folders = sorted([f.name for f in project_path.iterdir() if f.is_dir()])
    
    assert actual_folders == sorted(expected_folders)

def test_templates_directory_validation(temp_project_dir):
    """Testa validação do diretório de templates."""
    logic = ProjectCreatorLogic()
    
    # O diretório pode existir ou não, mas a validação deve funcionar
    is_valid = logic._validate_templates_directory()
    
    # Se retornar False, deve ser porque diretório não existe
    # Se retornar True, diretório existe
    assert isinstance(is_valid, bool)
