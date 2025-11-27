"""Script para exibir relatório de uso de tokens."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.token_monitor import TokenMonitor


def format_number(num: int) -> str:
    """Formata número com separador de milhares."""
    return f"{num:,}".replace(",", ".")


def main():
    """Função principal para exibir relatório."""
    print("=" * 80)
    print("Relatório de Uso de Tokens")
    print("=" * 80)
    print()
    
    # Verificar se o banco existe
    db_path = "data/token_usage.db"
    if not os.path.exists(db_path):
        print("❌ Nenhum dado encontrado. Execute o agente primeiro.")
        return
    
    # Criar monitor para acessar o banco
    monitor = TokenMonitor(db_path=db_path)
    
    # Obter relatório completo
    report = monitor.get_report(limit=1000)
    
    if report["total_queries"] == 0:
        print("📭 Nenhuma query registrada ainda.")
        return
    
    # Estatísticas gerais
    print("📊 Estatísticas Gerais:")
    print(f"   Total de queries: {format_number(report['total_queries'])}")
    print(f"   Total de tokens: {format_number(report['total_tokens'])}")
    print(f"   Tokens de entrada: {format_number(report['total_input_tokens'])}")
    print(f"   Tokens de saída: {format_number(report['total_output_tokens'])}")
    print(f"   Média por query: {format_number(int(report['average_tokens_per_query']))}")
    print()
    
    # Últimas queries
    if report["recent_queries"]:
        print("📝 Últimas 10 Queries:")
        print("-" * 80)
        for i, query_data in enumerate(report["recent_queries"], 1):
            timestamp = query_data["timestamp"]
            query = query_data["query"][:50] + "..." if len(query_data["query"]) > 50 else query_data["query"]
            total_tokens = query_data["total_tokens"]
            
            print(f"{i:2d}. [{timestamp}] {query}")
            print(f"    Tokens: {format_number(total_tokens)} "
                  f"(In: {format_number(query_data['input_tokens'])}, "
                  f"Out: {format_number(query_data['output_tokens'])})")
            print()
    
    # Estatísticas por período (últimos 7 dias)
    print("📅 Estatísticas dos Últimos 7 Dias:")
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    weekly_report = monitor.get_report(start_date=seven_days_ago)
    print(f"   Queries: {format_number(weekly_report['total_queries'])}")
    print(f"   Tokens: {format_number(weekly_report['total_tokens'])}")
    print()
    
    # Estatísticas por período (últimas 24 horas)
    print("📅 Estatísticas das Últimas 24 Horas:")
    one_day_ago = (datetime.now() - timedelta(days=1)).isoformat()
    daily_report = monitor.get_report(start_date=one_day_ago)
    print(f"   Queries: {format_number(daily_report['total_queries'])}")
    print(f"   Tokens: {format_number(daily_report['total_tokens'])}")
    print()
    
    print("=" * 80)


if __name__ == "__main__":
    main()

