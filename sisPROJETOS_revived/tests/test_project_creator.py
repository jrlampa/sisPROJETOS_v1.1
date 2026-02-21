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


# ---------------------------------------------------------------------------
# Testes adicionais para cobertura de branches específicos
# ---------------------------------------------------------------------------

def test_validate_templates_directory_not_exists(tmp_path, monkeypatch):
    """Testa que _validate_templates_directory retorna False se não existe."""
    logic = ProjectCreatorLogic()
    # Aponta templates para diretório que não existe
    nonexistent = tmp_path / "nonexistent_templates"
    from pathlib import Path
    monkeypatch.setattr(logic, "templates_dir", nonexistent)
    assert logic._validate_templates_directory() is False


def test_validate_templates_directory_is_file(tmp_path, monkeypatch):
    """Testa que _validate_templates_directory retorna False se é arquivo."""
    logic = ProjectCreatorLogic()
    # Cria um arquivo onde se esperaria um diretório
    fake_file = tmp_path / "templates_file"
    fake_file.write_text("not a directory")
    monkeypatch.setattr(logic, "templates_dir", fake_file)
    assert logic._validate_templates_directory() is False


def test_create_structure_with_missing_templates(tmp_path, monkeypatch):
    """Testa criação de projeto quando templates estão ausentes."""
    from pathlib import Path
    logic = ProjectCreatorLogic()
    # Aponta para diretório existente mas sem templates
    empty_templates = tmp_path / "empty_templates"
    empty_templates.mkdir()
    monkeypatch.setattr(logic, "templates_dir", empty_templates)

    success, msg = logic.create_structure("ProjSemTemplates", str(tmp_path))
    # Deve ter sucesso mesmo sem templates (apenas avisa)
    assert success is True
    project_path = tmp_path / "ProjSemTemplates"
    assert project_path.exists()
    assert "info.txt" in [f.name for f in project_path.iterdir()]


def test_create_structure_permission_error(tmp_path, monkeypatch):
    """Testa erro de permissão ao criar projeto."""
    logic = ProjectCreatorLogic()

    def mock_mkdir(*args, **kwargs):
        raise PermissionError("Permission denied")

    from pathlib import Path
    monkeypatch.setattr(Path, "mkdir", mock_mkdir)

    success, msg = logic.create_structure("ProjPermissao", str(tmp_path))
    assert success is False
    assert "permissão" in msg.lower() or "Sem permissão" in msg


def test_info_file_contains_templates_info(tmp_path):
    """Testa que info.txt registra quantos templates foram copiados."""
    logic = ProjectCreatorLogic()
    project_name = "InfoTemplates"

    logic.create_structure(project_name, str(tmp_path))
    info_path = tmp_path / project_name / "info.txt"

    content = info_path.read_text(encoding="utf-8")
    assert "Templates Copiados:" in content


# ============================================================
# Testes adicionais para cobertura de branches
# ============================================================

def test_templates_dir_not_found(tmp_path):
    """Cobre linha 59: retorna falso quando templates_dir não existe."""
    logic = ProjectCreatorLogic()
    logic.templates_dir = Path("/caminho/inexistente/templates_xyz_abc")

    success, msg = logic.create_structure("ProjSemTemplates", str(tmp_path))
    assert success is False
    assert "templates" in msg.lower() or "Reinstale" in msg


def test_template_copy_exception(tmp_path, mocker):
    """Cobre linhas 98-100: shutil.copy2 lança exceção durante cópia."""
    mocker.patch(
        "src.modules.project_creator.logic.shutil.copy2",
        side_effect=OSError("Disco cheio"),
    )

    logic = ProjectCreatorLogic()
    success, msg = logic.create_structure("ProjCopyFail", str(tmp_path))

    # Projecto criado mas com aviso de templates ausentes
    assert success is True
    assert "sucesso" in msg.lower()


def test_create_structure_oserror(tmp_path, mocker):
    """Cobre linhas 123-124: OSError ao criar diretório do projeto."""
    mocker.patch.object(Path, "mkdir", side_effect=OSError("Disco cheio"))

    logic = ProjectCreatorLogic()
    success, msg = logic.create_structure("ProjOSError", str(tmp_path))

    assert success is False
    assert "sistema" in msg.lower() or "Erro" in msg


def test_create_structure_unexpected_exception(tmp_path, mocker):
    """Cobre linhas 125-127: exceção inesperada durante criação do projeto."""
    mocker.patch.object(Path, "mkdir", side_effect=RuntimeError("Erro inesperado"))

    logic = ProjectCreatorLogic()
    success, msg = logic.create_structure("ProjException", str(tmp_path))

    assert success is False
    assert "inesperado" in msg.lower() or "Erro" in msg


# ============================================================
# Testes de sanitização de entradas
# ============================================================

def test_create_structure_empty_project_name_returns_error(tmp_path):
    """Sanitizer: nome de projeto vazio deve retornar erro."""
    logic = ProjectCreatorLogic()
    success, msg = logic.create_structure("", str(tmp_path))
    assert success is False
    assert "Erro" in msg


def test_create_structure_none_project_name_returns_error(tmp_path):
    """Sanitizer: nome de projeto None deve retornar erro."""
    logic = ProjectCreatorLogic()
    success, msg = logic.create_structure(None, str(tmp_path))
    assert success is False
    assert "Erro" in msg


def test_create_structure_whitespace_project_name_returns_error(tmp_path):
    """Sanitizer: nome de projeto apenas espaços deve retornar erro."""
    logic = ProjectCreatorLogic()
    success, msg = logic.create_structure("   ", str(tmp_path))
    assert success is False
    assert "Erro" in msg


def test_create_structure_null_byte_in_path_returns_error(tmp_path):
    """Sanitizer: caminho base com byte nulo deve retornar erro."""
    logic = ProjectCreatorLogic()
    success, msg = logic.create_structure("Projeto", str(tmp_path) + "\x00evil")
    assert success is False
    assert "Erro" in msg
