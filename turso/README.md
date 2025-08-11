# Turso Agent A2A

Agente de persistência para o framework A2A usando Turso Database.

## Características

- ✅ Segue padrão A2A completo
- 💾 Persistência durável com Turso/LibSQL
- 🔄 Suporte a streaming
- 📊 Queries SQL customizadas
- ⏱️ Suporte a TTL (Time To Live)
- 🔐 Isolamento por agente e sessão

## Instalação

```bash
uv pip install -e .
```

## Uso

```bash
# Iniciar servidor
python server.py

# Ou com uv
uv run python server.py
```

## Estrutura

- `agent.py` - Implementação do agente Turso
- `agent_executor.py` - Executor seguindo padrão A2A
- `server.py` - Servidor A2A na porta 4243
- `test_a2a_integration.py` - Testes de integração

## Configuração

Configure as variáveis de ambiente no arquivo `.env`:

```env
TURSO_DATABASE_URL=file:local.db  # ou URL do Turso Cloud
TURSO_AUTH_TOKEN=                 # Token para Turso Cloud
PORT=4243                          # Porta do servidor
```

## Comandos Disponíveis

- `help` - Listar comandos disponíveis
- `store <key> <value>` - Armazenar dados
- `get <key>` - Recuperar dados
- `list` - Listar todas as chaves
- `stats` - Estatísticas do banco

## Integração A2A

Este agente está totalmente integrado com o framework A2A e pode ser usado com Claude Flow para coordenação de swarms.