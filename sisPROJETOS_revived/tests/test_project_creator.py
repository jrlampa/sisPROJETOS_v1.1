import pytest
import os
import shutil
from src.modules.project_creator.logic import ProjectCreatorLogic

@pytest.fixture
def temp_project_dir(tmp_path):
    return tmp_path / "test_project"

def test_create_structure(temp_project_dir):
    logic = ProjectCreatorLogic()
    # The project name should match what we expect to be created inside the parent
    project_name = "TestProj"
    # Logic will create folder at base_path/project_name
    success, msg = logic.create_structure(project_name, str(temp_project_dir.parent))
    
    expected_full_path = os.path.join(str(temp_project_dir.parent), project_name)
    
    assert success is True
    assert os.path.exists(expected_full_path)
    assert os.path.exists(os.path.join(expected_full_path, "1_Documentos"))
    assert os.path.exists(os.path.join(expected_full_path, "2_Desenhos", f"{project_name}_prancha.dwg"))

def test_create_structure_already_exists(temp_project_dir):
    logic = ProjectCreatorLogic()
    os.makedirs(temp_project_dir)
    
    success, msg = logic.create_structure("test_project", str(temp_project_dir.parent))
    assert success is False
    assert "já existe" in msg
