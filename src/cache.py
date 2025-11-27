"""Cache em memória para consultas ao GitHub."""

import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class QueryCache:
    """Cache em memória com TTL para reduzir chamadas à API do GitHub."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Inicializa o cache.
        
        Args:
            ttl_seconds: Tempo de vida do cache em segundos (default: 1 hora)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
    
    def _generate_key(self, query: str, repo_owner: str, repo_name: str) -> str:
        """
        Gera chave única para a query.
        
        Args:
            query: Pergunta do usuário
            repo_owner: Proprietário do repositório
            repo_name: Nome do repositório
            
        Returns:
            Hash MD5 da chave
        """
        key_string = f"{query}|{repo_owner}|{repo_name}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, repo_owner: str, repo_name: str) -> Optional[Any]:
        """
        Recupera valor do cache se ainda válido.
        
        Args:
            query: Pergunta do usuário
            repo_owner: Proprietário do repositório
            repo_name: Nome do repositório
            
        Returns:
            Valor em cache ou None se não encontrado/expirado
        """
        key = self._generate_key(query, repo_owner, repo_name)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        timestamp = entry["timestamp"]
        
        # Verificar se expirou
        if datetime.now() - timestamp > timedelta(seconds=self.ttl):
            del self.cache[key]
            return None
        
        return entry["value"]
    
    def set(self, query: str, repo_owner: str, repo_name: str, value: Any):
        """
        Armazena valor no cache.
        
        Args:
            query: Pergunta do usuário
            repo_owner: Proprietário do repositório
            repo_name: Nome do repositório
            value: Valor a armazenar
        """
        key = self._generate_key(query, repo_owner, repo_name)
        
        self.cache[key] = {
            "value": value,
            "timestamp": datetime.now()
        }
    
    def clear(self):
        """Limpa todo o cache."""
        self.cache.clear()
    
    def clear_expired(self):
        """Remove apenas entradas expiradas."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry["timestamp"] > timedelta(seconds=self.ttl)
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas
        """
        self.clear_expired()
        return {
            "total_entries": len(self.cache),
            "ttl_seconds": self.ttl
        }

