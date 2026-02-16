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
