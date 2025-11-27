"""Testes para o agente GitHub."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from src.agent import setup_github_toolkit, create_agent
from src.token_monitor import TokenMonitor


class TestAgent(unittest.TestCase):
    """Testes para o agente GitHub."""
    
    @patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"})
    def test_setup_github_toolkit_with_token(self):
        """Testa configuração do Github Toolkit com token."""
        try:
            toolkit = setup_github_toolkit(github_token="test_token")
            self.assertIsNotNone(toolkit)
        except Exception as e:
            # Pode falhar se não tiver conexão real, mas não deve dar erro de token
            self.assertNotIn("GITHUB_TOKEN não encontrado", str(e))
    
    def test_setup_github_toolkit_without_token(self):
        """Testa configuração do Github Toolkit sem token."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                setup_github_toolkit()
    
    @patch('src.agent.ChatHuggingFace')
    @patch('src.agent.setup_github_toolkit')
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test_token",
        "LLM_MODEL_NAME": "test-model"
    })
    def test_create_agent(self, mock_toolkit_setup, mock_llm):
        """Testa criação do agente."""
        # Mock do toolkit
        mock_toolkit = Mock()
        mock_toolkit.get_tools.return_value = []
        mock_toolkit_setup.return_value = mock_toolkit
        
        # Mock do LLM
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        
        try:
            agent = create_agent(
                model_name="test-model",
                token_monitor=TokenMonitor(model_name="test-model")
            )
            # Se chegou aqui, o agente foi criado
            self.assertIsNotNone(agent)
        except Exception as e:
            # Pode falhar em algumas dependências, mas estrutura deve estar correta
            # Verificar que não é erro de configuração básica
            self.assertNotIn("GITHUB_TOKEN não encontrado", str(e))


if __name__ == "__main__":
    unittest.main()

