# Agente GitHub Toolkit

Agente baseado em LangChain capaz de acessar repositórios no GitHub e responder perguntas sobre issues, commits, pull requests e conteúdos de arquivos. O agente utiliza a Github Toolkit do LangChain para consultas diretas na API do GitHub e apresenta monitoramento da quantidade de tokens utilizados em cada interação.

## Características

- Consultas inteligentes sobre repositórios GitHub
- Monitoramento detalhado de consumo de tokens
- Cache de consultas para reduzir chamadas à API
- Suporte a modelos HuggingFace (local ou na nuvem)
- Histórico persistente de interações
- Respostas com citação de fontes (issues, commits, arquivos)

## Requisitos

- Python 3.10 ou superior
- Conta no GitHub com token de acesso
- (Opcional) Token do HuggingFace para modelos privados
- Acesso à internet durante execução

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd Agente-Github-Toolkit
```

### 2. Crie e ative um ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e configure suas credenciais:

```bash
# Windows
copy config\env.example .env

# Linux/Mac
cp config/env.example .env
```

Edite o arquivo `.env` e configure:

```env
# Token do GitHub (obrigatório)
# Obtenha em: https://github.com/settings/tokens
# Permissões necessárias: repo (read-only)
GITHUB_TOKEN=seu_token_aqui

# Token do HuggingFace (opcional, apenas para modelos privados)
HUGGINGFACE_API_TOKEN=

# Repositório alvo
REPO_OWNER=langchain-ai
REPO_NAME=langchain

# Modelo LLM (HuggingFace)
LLM_MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2
```

### 5. Obter Token do GitHub

1. Acesse [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens)
2. Clique em "Generate new token (classic)"
3. Selecione o escopo `repo` (read-only é suficiente)
4. Copie o token e cole no arquivo `.env`

## Uso

### Executar o Agente

```bash
python scripts/run_agent.py
```

O agente iniciará em modo interativo. Digite suas perguntas sobre o repositório:

```
❓ Pergunta: Quais issues abertas têm a label 'bug'?
❓ Pergunta: Qual foi a mudança no arquivo README.md no último commit?
❓ Pergunta: Quem foi o autor do último pull request mergeado?
```

Digite `sair` ou `exit` para encerrar.

### Ver Relatório de Tokens

```bash
python scripts/show_token_report.py
```

Este script exibe:
- Total de queries executadas
- Total de tokens consumidos
- Estatísticas por período (últimas 24h, últimos 7 dias)
- Histórico das últimas queries

## Exemplos de Perguntas

O agente pode responder perguntas como:

### Issues
- "Quais issues abertas têm a label 'bug'?"
- "Liste todas as issues fechadas na última semana"
- "Mostre os detalhes da issue #123"

### Commits
- "Qual foi a mudança no arquivo src/main.py no último commit?"
- "Quantos commits foram feitos na última semana?"
- "Quais arquivos foram modificados no commit abc123?"

### Pull Requests
- "Quem foi o autor do último pull request mergeado?"
- "Liste todos os PRs abertos"
- "Mostre os detalhes do PR #456"

### Arquivos
- "Mostre o conteúdo do arquivo README.md"
- "Qual foi o último commit que alterou o arquivo src/config.py?"
- "Liste todos os arquivos na pasta docs/"

## Arquitetura

```
Agente-Github-Toolkit/
├── src/
│   ├── agent.py              # Agente LangChain principal
│   ├── token_monitor.py      # Monitoramento de tokens
│   ├── prompts.py            # System prompts e few-shot examples
│   └── cache.py              # Cache de consultas
├── scripts/
│   ├── run_agent.py          # Script principal
│   └── show_token_report.py  # Relatório de tokens
├── tests/                    # Testes automatizados
├── data/                     # Banco de dados SQLite (gerado automaticamente)
└── config/                   # Configurações
```

### Componentes Principais

1. **Agent (`src/agent.py`)**: Orquestra interações com o LLM e Github Toolkit
2. **TokenMonitor (`src/token_monitor.py`)**: Rastreia e persiste consumo de tokens
3. **Prompts (`src/prompts.py`)**: Define comportamento e exemplos few-shot
4. **Cache (`src/cache.py`)**: Reduz chamadas desnecessárias à API do GitHub

## Decisões de Design

### Provedor LLM: HuggingFace
- Suporte a modelos open-source
- Flexibilidade para usar modelos locais ou na nuvem
- Contagem precisa de tokens via tokenizer

### Banco de Dados: SQLite
- Simplicidade e portabilidade
- Sem dependências externas
- Adequado para histórico de uso

### Cache: Em Memória
- Reduz chamadas à API do GitHub
- TTL configurável (padrão: 1 hora)
- Pode ser expandido para Redis se necessário

## Troubleshooting

### Erro: "GITHUB_TOKEN não encontrado"
- Verifique se o arquivo `.env` existe e contém `GITHUB_TOKEN`
- Certifique-se de que o token tem permissões de leitura no repositório

### Erro ao carregar modelo HuggingFace
- Verifique se o nome do modelo está correto
- Para modelos grandes, certifique-se de ter memória suficiente
- Considere usar modelos menores ou HuggingFaceEndpoint para modelos na nuvem

### Rate Limiting do GitHub
- O agente implementa cache para reduzir chamadas
- Se necessário, aguarde alguns minutos entre consultas
- Considere aumentar o TTL do cache

### Erro de conexão
- Verifique sua conexão com a internet
- Confirme que o repositório existe e é acessível
- Verifique se o token do GitHub não expirou

## Desenvolvimento

### Executar Testes

```bash
python -m pytest tests/
```

Ou usando unittest:

```bash
python -m unittest discover tests
```

### Estrutura de Testes

- `tests/test_token_monitor.py`: Testes do monitor de tokens
- `tests/test_agent.py`: Testes do agente (com mocks)

## Segurança

⚠️ **Importante**:
- Nunca commite o arquivo `.env` no repositório
- Use tokens com escopo mínimo necessário (read-only)
- Mantenha seus tokens seguros e rotacione-os periodicamente

O arquivo `.gitignore` já está configurado para excluir `.env` e dados sensíveis.

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Referências

- [LangChain Documentation](https://python.langchain.com/)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)

## Suporte

Para questões e problemas, abra uma issue no repositório.
