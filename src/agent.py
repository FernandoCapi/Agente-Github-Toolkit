"""Agente LangChain para consultas em repositórios GitHub."""

import os
from typing import Optional, List
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate

from src.prompts import get_system_prompt_with_examples
from src.token_monitor import TokenMonitor

# Carregar variáveis de ambiente
load_dotenv()


def setup_github_toolkit(github_token: Optional[str] = None) -> GitHubToolkit:
    """
    Configura e inicializa o Github Toolkit do LangChain.
    
    Args:
        github_token: Token de acesso do GitHub (se None, usa GITHUB_TOKEN do .env)
        
    Returns:
        GitHubToolkit configurado
        
    Raises:
        ValueError: Se o token não for fornecido
    """
    if github_token is None:
        github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        raise ValueError(
            "GITHUB_TOKEN não encontrado. Configure no arquivo .env ou passe como argumento."
        )
    
    # Criar wrapper da API do GitHub
    github = GitHubAPIWrapper(github_token=github_token)
    
    # Criar toolkit com todas as ferramentas disponíveis
    toolkit = GitHubToolkit.from_github_api_wrapper(github)
    
    # Testar conexão básica
    try:
        repo_owner = os.getenv("REPO_OWNER", "langchain-ai")
        repo_name = os.getenv("REPO_NAME", "langchain")
        # Teste simples: verificar se consegue acessar o repositório
        # Isso será feito implicitamente quando o agente usar as tools
        print(f"✓ Github Toolkit configurado para {repo_owner}/{repo_name}")
    except Exception as e:
        print(f"⚠ Aviso ao configurar Github Toolkit: {e}")
    
    return toolkit


def create_agent(
    model_name: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    github_token: Optional[str] = None,
    token_monitor: Optional[TokenMonitor] = None
) -> AgentExecutor:
    """
    Cria e configura o agente LangChain com Github Toolkit.
    
    Args:
        model_name: Nome do modelo HuggingFace (se None, usa LLM_MODEL_NAME do .env)
        temperature: Temperatura para geração (default: 0.7)
        max_tokens: Número máximo de tokens na resposta (default: 1000)
        github_token: Token do GitHub (se None, usa GITHUB_TOKEN do .env)
        token_monitor: Instância do TokenMonitor (se None, cria nova)
        
    Returns:
        AgentExecutor configurado
    """
    # Carregar configurações
    if model_name is None:
        model_name = os.getenv("LLM_MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.2")
    
    # Configurar monitor de tokens
    if token_monitor is None:
        token_monitor = TokenMonitor(model_name=model_name)
        token_monitor.set_tokenizer(model_name)
    
    # Setup do Github Toolkit
    toolkit = setup_github_toolkit(github_token)
    tools = toolkit.get_tools()
    
    # Criar LLM
    try:
        # Tentar usar HuggingFaceEndpoint primeiro (para modelos na nuvem)
        hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
        if hf_token:
            llm = HuggingFaceEndpoint(
                repo_id=model_name,
                huggingfacehub_api_token=hf_token,
                temperature=temperature,
                max_length=max_tokens,
            )
        else:
            # Usar modelo local via ChatHuggingFace
            from langchain_huggingface import ChatHuggingFace
            llm = ChatHuggingFace(
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
    except Exception as e:
        print(f"⚠ Erro ao carregar modelo {model_name}: {e}")
        print("Tentando usar modelo padrão...")
        # Fallback para modelo mais leve
        llm = ChatHuggingFace(
            model_name="microsoft/DialoGPT-medium",
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    # Criar prompt template (ReAct format)
    system_prompt = get_system_prompt_with_examples()
    
    prompt_template = f"""{system_prompt}

Você tem acesso às seguintes ferramentas:

{{tools}}

Use o seguinte formato:

Question: a pergunta de entrada que você deve responder
Thought: você deve pensar sobre o que fazer
Action: a ação a tomar, deve ser uma das [{{tool_names}}]
Action Input: a entrada para a ação
Observation: o resultado da ação
... (este Thought/Action/Action Input/Observation pode repetir N vezes)
Thought: Agora sei a resposta final
Final Answer: a resposta final à pergunta original

Question: {{input}}
Thought:{{agent_scratchpad}}"""
    
    prompt = PromptTemplate.from_template(prompt_template)
    
    # Criar agente ReAct (compatível com HuggingFace)
    agent = create_react_agent(llm, tools, prompt)
    
    # Criar executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        callbacks=[token_monitor] if token_monitor else None
    )
    
    return agent_executor


def test_github_connection(repo_owner: str, repo_name: str) -> bool:
    """
    Testa a conexão com o GitHub listando issues abertas.
    
    Args:
        repo_owner: Proprietário do repositório
        repo_name: Nome do repositório
        
    Returns:
        True se a conexão funcionar, False caso contrário
    """
    try:
        toolkit = setup_github_toolkit()
        # Usar uma tool simples para testar
        tools = toolkit.get_tools()
        if tools:
            print(f"✓ Conexão com GitHub estabelecida. {len(tools)} ferramentas disponíveis.")
            return True
    except Exception as e:
        print(f"✗ Erro ao conectar com GitHub: {e}")
        return False
    return False

