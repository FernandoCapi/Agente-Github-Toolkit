"""Monitor de tokens para rastrear consumo em interações com LLM."""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult
from transformers import AutoTokenizer


class TokenMonitor(BaseCallbackHandler):
    """Monitor que rastreia tokens consumidos e persiste em SQLite."""
    
    def __init__(self, db_path: str = "data/token_usage.db", model_name: str = ""):
        """
        Inicializa o monitor de tokens.
        
        Args:
            db_path: Caminho para o banco de dados SQLite
            model_name: Nome do modelo LLM sendo usado
        """
        self.db_path = db_path
        self.model_name = model_name
        self.current_session_tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "queries": 0
        }
        self.current_query: Optional[str] = None
        self.tokenizer: Optional[Any] = None
        
        # Criar diretório se não existir
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar banco de dados
        self._init_database()
    
    def _init_database(self):
        """Cria a tabela de histórico de tokens se não existir."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_query TEXT,
                response_length INTEGER,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                model_name TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def set_tokenizer(self, model_name: str):
        """
        Configura o tokenizer para contagem precisa de tokens.
        
        Args:
            model_name: Nome do modelo HuggingFace
        """
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model_name = model_name
        except Exception as e:
            print(f"Warning: Não foi possível carregar tokenizer para {model_name}: {e}")
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """
        Conta tokens em um texto usando o tokenizer.
        
        Args:
            text: Texto para contar tokens
            
        Returns:
            Número de tokens
        """
        if self.tokenizer is None:
            # Fallback: estimativa aproximada (1 token ≈ 4 caracteres)
            return len(text) // 4
        return len(self.tokenizer.encode(text))
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Chamado quando o LLM inicia."""
        if prompts:
            # Contar tokens de entrada
            input_text = " ".join(prompts)
            input_tokens = self.count_tokens(input_text)
            self.current_session_tokens["input_tokens"] += input_tokens
    
    def on_llm_end(self, response: LLMResult, **kwargs):
        """Chamado quando o LLM termina."""
        if response.generations:
            # Contar tokens de saída
            output_text = " ".join([gen[0].text for gen in response.generations if gen])
            output_tokens = self.count_tokens(output_text)
            self.current_session_tokens["output_tokens"] += output_tokens
            self.current_session_tokens["total_tokens"] = (
                self.current_session_tokens["input_tokens"] + 
                self.current_session_tokens["output_tokens"]
            )
    
    def log_query(self, user_query: str, response_text: str, 
                  input_tokens: Optional[int] = None, 
                  output_tokens: Optional[int] = None):
        """
        Registra uma query completa no banco de dados.
        
        Args:
            user_query: Pergunta do usuário
            response_text: Resposta do agente
            input_tokens: Tokens de entrada (se None, calcula automaticamente)
            output_tokens: Tokens de saída (se None, calcula automaticamente)
        """
        if input_tokens is None:
            input_tokens = self.count_tokens(user_query)
        if output_tokens is None:
            output_tokens = self.count_tokens(response_text)
        
        total_tokens = input_tokens + output_tokens
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO token_usage 
            (timestamp, user_query, response_length, input_tokens, output_tokens, total_tokens, model_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            user_query,
            len(response_text),
            input_tokens,
            output_tokens,
            total_tokens,
            self.model_name
        ))
        conn.commit()
        conn.close()
        
        self.current_session_tokens["queries"] += 1
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da sessão atual.
        
        Returns:
            Dicionário com estatísticas da sessão
        """
        return {
            "input_tokens": self.current_session_tokens["input_tokens"],
            "output_tokens": self.current_session_tokens["output_tokens"],
            "total_tokens": self.current_session_tokens["total_tokens"],
            "queries": self.current_session_tokens["queries"]
        }
    
    def get_report(self, limit: int = 100, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Gera relatório agregado de uso de tokens.
        
        Args:
            limit: Número máximo de registros a retornar
            start_date: Data inicial (ISO format)
            end_date: Data final (ISO format)
            
        Returns:
            Dicionário com estatísticas agregadas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM token_usage WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Calcular estatísticas
        total_input = sum(row[5] for row in rows)  # input_tokens
        total_output = sum(row[6] for row in rows)  # output_tokens
        total_tokens = sum(row[7] for row in rows)  # total_tokens
        total_queries = len(rows)
        
        conn.close()
        
        return {
            "total_queries": total_queries,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_tokens,
            "average_tokens_per_query": total_tokens / total_queries if total_queries > 0 else 0,
            "recent_queries": [
                {
                    "timestamp": row[1],
                    "query": row[2],
                    "input_tokens": row[5],
                    "output_tokens": row[6],
                    "total_tokens": row[7]
                }
                for row in rows[:10]  # Últimas 10 queries
            ]
        }
    
    def reset_session(self):
        """Reseta as estatísticas da sessão atual."""
        self.current_session_tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "queries": 0
        }

