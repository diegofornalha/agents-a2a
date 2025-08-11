# Turso Agent - Padrão A2A

## 📦 Sobre

Agente A2A para persistência de dados usando Turso Database, seguindo o padrão oficial A2A com SDK.

## ✅ Conformidade A2A

Este agente está **100% em conformidade** com o padrão A2A estabelecido pelo Marvin:

- ✅ Usa `a2a-sdk` oficial
- ✅ Implementa `AgentExecutor` com `invoke()` e `stream()`
- ✅ Usa `A2AStarletteApplication` para o servidor
- ✅ Implementa `DefaultRequestHandler` e `InMemoryTaskStore`
- ✅ Agent Card com classes oficiais do SDK
- ✅ Suporte a streaming de respostas

## 🚀 Instalação

```bash
# Instalar uv se necessário
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependências
uv sync
```

## 🔧 Configuração

1. Copie `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Configure as variáveis de ambiente conforme necessário.

## 🎯 Execução

### Método 1: Script de inicialização
```bash
./run.sh
```

### Método 2: Direto com uv
```bash
uv run python server.py
```

### Método 3: Com porta customizada
```bash
PORT=4243 uv run python server.py
```

## 📝 Estrutura do Projeto (Padrão A2A)

```
turso/
├── __init__.py          # Módulo Python
├── agent.py            # Classe TursoAgent com lógica de negócio
├── agent_executor.py   # TursoAgentExecutor implementando padrão A2A
├── server.py          # Servidor usando A2AStarletteApplication
├── pyproject.toml     # Dependências incluindo a2a-sdk
├── run.sh            # Script de inicialização
└── README_A2A.md     # Esta documentação
```

## 🔌 Endpoints A2A

O agente expõe os endpoints padrão A2A:

- `GET /` - Informações do agente
- `GET /health` - Status de saúde
- `GET /.well-known/agent.json` - Agent Card
- `POST /invoke` - Invocar agente (padrão A2A)
- `POST /stream` - Stream de respostas (padrão A2A)

## 💾 Operações Suportadas

### 1. Armazenar Dados
```json
{
  "operation": "store",
  "key": "user_123",
  "value": {"name": "João", "email": "joao@example.com"},
  "ttl": 3600
}
```

### 2. Recuperar Dados
```json
{
  "operation": "retrieve",
  "key": "user_123"
}
```

### 3. Query SQL
```json
{
  "operation": "query",
  "sql": "SELECT * FROM agent_data WHERE agent_id = ?"
}
```

### 4. Comandos de Texto
- `help` - Exibir ajuda
- `list` - Listar todas as chaves
- `stats` - Estatísticas do banco
- `store <key> <value>` - Armazenar via texto
- `get <key>` - Recuperar via texto

## 🔄 Integração com Outros Agentes

Por estar em conformidade com o padrão A2A, o Turso Agent pode:

1. **Se comunicar com outros agentes A2A** (como o Marvin)
2. **Ser descoberto** via Agent Card
3. **Processar requisições** no formato A2A padrão
4. **Fazer streaming** de respostas
5. **Gerenciar tarefas** com InMemoryTaskStore

## 🧪 Testando

```bash
# Teste básico
curl http://localhost:4243/

# Agent Card
curl http://localhost:4243/.well-known/agent.json

# Health check
curl http://localhost:4243/health

# Invocar agente (padrão A2A)
curl -X POST http://localhost:4243/invoke \
  -H "Content-Type: application/json" \
  -d '{"query": "help", "sessionId": "test-123"}'
```

## 📊 Diferenças da Versão Antiga

| Aspecto | Versão Antiga (FastAPI) | Nova Versão (A2A) |
|---------|------------------------|-------------------|
| Framework | FastAPI puro | A2A SDK + Starlette |
| Padrão | REST customizado | A2A oficial |
| Agent Card | Dicionário manual | Classes A2A |
| Executor | Não tinha | TursoAgentExecutor |
| Streaming | Não suportado | Suportado |
| Task Store | Não tinha | InMemoryTaskStore |

## 🛠️ Desenvolvimento

Para adicionar novas funcionalidades, siga o padrão A2A:

1. Adicione a lógica em `agent.py` no método `invoke()`
2. Atualize o `agent_executor.py` se necessário
3. Adicione skills no Agent Card em `server.py`
4. Mantenha compatibilidade com o SDK A2A

## 📚 Referências

- [A2A SDK Documentation](https://github.com/a2a/sdk)
- [Marvin Agent](../marvin/) - Exemplo de referência
- [Turso Database](https://turso.tech)