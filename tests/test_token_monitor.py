"""Testes para o TokenMonitor."""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from src.token_monitor import TokenMonitor


class TestTokenMonitor(unittest.TestCase):
    """Testes para a classe TokenMonitor."""
    
    def setUp(self):
        """Configuração antes de cada teste."""
        # Criar diretório temporário para banco de dados
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_token_usage.db")
        self.monitor = TokenMonitor(db_path=self.db_path, model_name="test-model")
    
    def tearDown(self):
        """Limpeza após cada teste."""
        # Remover diretório temporário
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_init_database(self):
        """Testa inicialização do banco de dados."""
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_count_tokens_without_tokenizer(self):
        """Testa contagem de tokens sem tokenizer (fallback)."""
        text = "Hello world, this is a test."
        tokens = self.monitor.count_tokens(text)
        # Fallback usa estimativa (1 token ≈ 4 caracteres)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, len(text))
    
    def test_log_query(self):
        """Testa registro de query no banco."""
        query = "Test query"
        response = "Test response"
        
        self.monitor.log_query(query, response, input_tokens=10, output_tokens=20)
        
        # Verificar se foi salvo
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM token_usage")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)
    
    def test_get_session_stats(self):
        """Testa obtenção de estatísticas da sessão."""
        stats = self.monitor.get_session_stats()
        
        self.assertIn("input_tokens", stats)
        self.assertIn("output_tokens", stats)
        self.assertIn("total_tokens", stats)
        self.assertIn("queries", stats)
    
    def test_get_report(self):
        """Testa geração de relatório."""
        # Adicionar algumas queries
        for i in range(5):
            self.monitor.log_query(
                f"Query {i}",
                f"Response {i}",
                input_tokens=10 + i,
                output_tokens=20 + i
            )
        
        report = self.monitor.get_report(limit=10)
        
        self.assertEqual(report["total_queries"], 5)
        self.assertGreater(report["total_tokens"], 0)
        self.assertEqual(len(report["recent_queries"]), 5)
    
    def test_reset_session(self):
        """Testa reset da sessão."""
        # Adicionar algumas queries
        self.monitor.log_query("Test", "Response", input_tokens=10, output_tokens=20)
        
        # Reset
        self.monitor.reset_session()
        
        stats = self.monitor.get_session_stats()
        self.assertEqual(stats["queries"], 0)
        self.assertEqual(stats["total_tokens"], 0)


if __name__ == "__main__":
    unittest.main()

