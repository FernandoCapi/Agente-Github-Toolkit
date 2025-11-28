"""Script principal para executar o agente GitHub."""

import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
from src.agent import create_agent, test_github_connection
from src.token_monitor import TokenMonitor
from src.cache import QueryCache

# Carregar variáveis de ambiente
load_dotenv()


def main():
    """Função principal para executar o agente."""
    print("=" * 60)
    print("Agente GitHub - LangChain")
    print("=" * 60)
    print()
    
    # Verificar variáveis de ambiente
    github_token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("REPO_OWNER", "langchain-ai")
    repo_name = os.getenv("REPO_NAME", "langchain")
    model_name = os.getenv("LLM_MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.2")
    
    if not github_token:
        print("❌ Erro: GITHUB_TOKEN não configurado!")
        print("Configure no arquivo .env ou como variável de ambiente.")
        return
    
    print(f"📦 Repositório: {repo_owner}/{repo_name}")
    print(f"🤖 Modelo: {model_name}")
    print()
    
    # Testar conexão com GitHub
    print("🔌 Testando conexão com GitHub...")
    if not test_github_connection(repo_owner, repo_name):
        print("❌ Falha ao conectar com GitHub. Verifique o token.")
        return
    
    # Inicializar componentes
    print("⚙️  Inicializando agente...")
    token_monitor = TokenMonitor(model_name=model_name)
    token_monitor.set_tokenizer(model_name)
    
    cache = QueryCache(ttl_seconds=3600)
    
    try:
        agent = create_agent(
            model_name=model_name,
            token_monitor=token_monitor
        )
        print("✓ Agente inicializado com sucesso!")
        print()
    except Exception as e:
        print(f"❌ Erro ao inicializar agente: {e}")
        return
    
    # Loop interativo
    print("💬 Digite suas perguntas sobre o repositório (ou 'sair' para encerrar)")
    print("-" * 60)
    
    while True:
        try:
            query = input("\n❓ Pergunta: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['sair', 'exit', 'quit', 'q']:
                print("\n👋 Encerrando...")
                break
            
            # Verificar cache
            cached_response = cache.get(query, repo_owner, repo_name)
            if cached_response:
                print("\n📦 Resposta (do cache):")
                print(cached_response)
                print("\n💡 Esta resposta foi recuperada do cache.")
                continue
            
            # Executar agente
            print("\n🔍 Processando...")
            try:
                response = agent.invoke({"input": query})
                answer = response.get("output", "Sem resposta")
                
                print("\n📝 Resposta:")
                print(answer)
                
                # Salvar no cache
                cache.set(query, repo_owner, repo_name, answer)
                
                # Mostrar estatísticas de tokens
                session_stats = token_monitor.get_session_stats()
                print("\n📊 Estatísticas de Tokens:")
                print(f"   Input: {session_stats['input_tokens']}")
                print(f"   Output: {session_stats['output_tokens']}")
                print(f"   Total: {session_stats['total_tokens']}")
                print(f"   Queries: {session_stats['queries']}")
                
                # Registrar query completa
                token_monitor.log_query(query, answer)
                
            except Exception as e:
                print(f"\n❌ Erro ao processar: {e}")
                print("Tente reformular sua pergunta.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Encerrando...")
            break
        except EOFError:
            print("\n\n👋 Encerrando...")
            break
    
    # Estatísticas finais
    print("\n" + "=" * 60)
    print("📊 Estatísticas Finais da Sessão:")
    final_stats = token_monitor.get_session_stats()
    print(f"   Total de queries: {final_stats['queries']}")
    print(f"   Total de tokens: {final_stats['total_tokens']}")
    print(f"   Tokens de entrada: {final_stats['input_tokens']}")
    print(f"   Tokens de saída: {final_stats['output_tokens']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

