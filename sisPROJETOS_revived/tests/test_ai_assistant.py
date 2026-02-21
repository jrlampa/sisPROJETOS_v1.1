import pytest
from unittest.mock import MagicMock, patch
from src.modules.ai_assistant.logic import AIAssistantLogic

@patch('src.modules.ai_assistant.logic.Groq')
def test_ai_assistant_get_response(mock_groq):
    # Setup mock
    instance = mock_groq.return_value
    instance.chat.completions.create.return_value.choices[0].message.content = "Resposta simulada"
    
    logic = AIAssistantLogic()
    logic.client = instance # Force mock client
    
    resp = logic.get_response("Olá")
    assert resp == "Resposta simulada"
    assert instance.chat.completions.create.called

def test_ai_assistant_no_api_key():
    with patch('os.getenv', return_value=None):
        logic = AIAssistantLogic()
        logic.client = None
        resp = logic.get_response("Olá")
        assert "Erro" in resp
        assert "Chave API" in resp


@patch('src.modules.ai_assistant.logic.Groq')
def test_ai_assistant_get_response_with_history(mock_groq):
    """Testa resposta com histórico de conversa."""
    instance = mock_groq.return_value
    instance.chat.completions.create.return_value.choices[0].message.content = "Resposta com histórico"

    logic = AIAssistantLogic()
    logic.client = instance

    history = [
        ("Pergunta anterior", "Resposta anterior"),
        ("Outra pergunta", "Outra resposta"),
    ]
    resp = logic.get_response("Nova pergunta", history=history)
    assert resp == "Resposta com histórico"

    # Verify the API was called with history messages
    call_args = instance.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    # system + 2 pairs of history (4) + 1 user = 6 messages
    assert len(messages) >= 5


def _get_messages_from_call(mock_instance):
    """Helper para extrair mensagens da chamada mock da API Groq."""
    return mock_instance.chat.completions.create.call_args.kwargs["messages"]


@patch('src.modules.ai_assistant.logic.Groq')
def test_ai_assistant_get_response_with_project_context(mock_groq):
    """Testa resposta com contexto de projeto."""
    instance = mock_groq.return_value
    instance.chat.completions.create.return_value.choices[0].message.content = "Resposta com contexto"

    logic = AIAssistantLogic()
    logic.client = instance

    project_context = {
        "pole_load": {"resultant_force": 500.0, "resultant_angle": 45.0},
        "catenary": {"sag": 2.5, "tension": 300},
        "electrical": {"percentage_drop": 3.2, "current": 15.0},
        "cqt": {"success": True, "summary": {"max_cqt": 4.5, "total_kva": 75.0}},
    }
    resp = logic.get_response("Análise do projeto", project_context=project_context)
    assert resp == "Resposta com contexto"

    # Verify context was included in the system prompt
    messages = _get_messages_from_call(instance)
    system_content = messages[0]["content"]
    assert "500.00 daN" in system_content
    assert "2.50m" in system_content
    assert "3.20%" in system_content
    assert "4.50%" in system_content


@patch('src.modules.ai_assistant.logic.Groq')
def test_ai_assistant_get_response_api_exception(mock_groq):
    """Testa que exceção da API retorna mensagem de erro formatada."""
    instance = mock_groq.return_value
    instance.chat.completions.create.side_effect = Exception("API quota exceeded")

    logic = AIAssistantLogic()
    logic.client = instance

    resp = logic.get_response("Consulta qualquer")
    assert "Erro" in resp
    assert "Groq AI" in resp


@patch('src.modules.ai_assistant.logic.Groq')
def test_ai_assistant_get_response_partial_context(mock_groq):
    """Testa contexto de projeto com apenas alguns campos preenchidos."""
    instance = mock_groq.return_value
    instance.chat.completions.create.return_value.choices[0].message.content = "OK"

    logic = AIAssistantLogic()
    logic.client = instance

    # Only pole_load in context
    project_context = {
        "pole_load": {"resultant_force": 200.0, "resultant_angle": 30.0},
    }
    resp = logic.get_response("Mensagem", project_context=project_context)
    assert resp == "OK"


@patch('src.modules.ai_assistant.logic.Groq')
def test_ai_assistant_model_is_configured(mock_groq):
    """Testa que o modelo de IA está configurado corretamente."""
    logic = AIAssistantLogic()
    assert logic.model == "llama-3.3-70b-versatile"


@patch('src.modules.ai_assistant.logic.Groq')
def test_ai_assistant_system_prompt_is_in_pt_br(mock_groq):
    """Testa que o prompt do sistema está em português."""
    logic = AIAssistantLogic()
    assert "engenharia" in logic.system_prompt.lower()
    assert "normas" in logic.system_prompt.lower()
