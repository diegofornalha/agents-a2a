# 🚨 PADRÃO OBRIGATÓRIO PARA AGENTES A2A

## ⚠️ ATENÇÃO CRÍTICA: SEMPRE USE server.py NO PADRÃO A2A

Este documento define o **PADRÃO OBRIGATÓRIO** para todos os agentes A2A neste projeto. **TODOS** os agentes **DEVEM** seguir esta estrutura para funcionar corretamente.

---

## 📋 Estrutura Obrigatória de Arquivos

Cada agente A2A **DEVE** ter os seguintes arquivos:

```
nome-do-agente/
├── server.py           # ✅ OBRIGATÓRIO - Ponto de entrada do servidor
├── agent.py            # ✅ OBRIGATÓRIO - Lógica do agente
├── agent_executor.py   # ✅ OBRIGATÓRIO - Executor padrão A2A
├── pyproject.toml      # ✅ OBRIGATÓRIO - Dependências do projeto
└── .env                # Opcional - Variáveis de ambiente
```

### ❌ NUNCA USE:
- `app.py` com FastAPI simples
- `main.py` sem o padrão A2A
- Servidores HTTP customizados
- Implementações que não usem o SDK A2A

---

## 🎯 Estrutura Padrão do server.py

**TODOS** os arquivos `server.py` **DEVEM** seguir este padrão:

```python
#!/usr/bin/env python3
"""
Servidor A2A para o [Nome do Agente]
Porta: [PORTA]
"""

import asyncio
import uvicorn
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório pai ao path se necessário
sys.path.append(str(Path(__file__).parent.parent.parent))

# ✅ IMPORTAÇÕES LOCAIS - SEMPRE RELATIVOS
from agent import [SeuAgente]
from agent_executor import [SeuAgentExecutor]

# ✅ IMPORTAÇÕES A2A - SEMPRE ESTAS
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def get_agent_card(host: str, port: int) -> AgentCard:
    """Retorna o Agent Card para o agente seguindo padrão A2A"""
    
    capabilities = AgentCapabilities(
        streaming=True  # Habilitar streaming se suportado
    )
    
    skills = [
        AgentSkill(
            id="skill_id",
            name="Nome da Skill",
            description="Descrição da skill",
            tags=["tag1", "tag2"],
            examples=["exemplo 1", "exemplo 2"],
        ),
        # Adicionar mais skills conforme necessário
    ]
    
    return AgentCard(
        name="Nome do Agente",
        description="Descrição do agente seguindo protocolo A2A",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text", "text/plain", "application/json"],
        defaultOutputModes=["text", "text/plain", "application/json"],
        capabilities=capabilities,
        skills=skills,
    )


def main():
    """Iniciar o servidor no padrão A2A"""
    
    # Configurações
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", XXXX))  # Definir porta
    
    print(f"🚀 Iniciando [Nome do Agente] (A2A) em {host}:{port}...")
    print(f"📦 Usando padrão A2A com SDK oficial")
    
    # ✅ CRIAR EXECUTOR - SEMPRE ASSIM
    agent_executor = [SeuAgentExecutor]()
    
    # ✅ CRIAR HANDLER - SEMPRE DefaultRequestHandler
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )
    
    # ✅ CRIAR SERVIDOR - SEMPRE A2AStarletteApplication
    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port),
        http_handler=request_handler
    )
    
    print("✅ Servidor configurado com padrão A2A")
    
    # ✅ INICIAR - SEMPRE com uvicorn
    uvicorn.run(
        server.build(),
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
```

---

## 🔧 Estrutura Padrão do agent_executor.py

**TODOS** os executores **DEVEM** herdar de `AgentExecutor` e implementar o método `execute`:

```python
import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import (
    new_agent_text_message,
    new_data_artifact,
    new_task,
    new_text_artifact,
)

class [SeuAgentExecutor](AgentExecutor):
    """Executor seguindo padrão A2A"""
    
    def __init__(self, agent):
        self.agent = agent
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Executar tarefa com gerenciamento completo de ciclo de vida"""
        
        # 1. Obter entrada e task
        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        # 2. Marcar como WORKING
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                status=TaskStatus(state=TaskState.working),
                final=False,
                contextId=task.contextId,
                taskId=task.id,
            )
        )
        
        # 3. Processar com o agente
        result = await self.agent.process(query, task.contextId)
        
        # 4. Criar artefato
        artifact = new_text_artifact(
            name="result",
            description="Resultado do processamento",
            text=result.get("text", "")
        )
        
        # 5. Enviar artefato
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                append=False,
                contextId=task.contextId,
                taskId=task.id,
                lastChunk=True,
                artifact=artifact,
            )
        )
        
        # 6. Marcar como COMPLETED
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                status=TaskStatus(state=TaskState.completed),
                final=True,
                contextId=task.contextId,
                taskId=task.id,
            )
        )
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancelar operação"""
        raise Exception("Cancel not supported")
```

---

## 🚀 Scripts de Inicialização

### ✅ SEMPRE no start_all_agents.sh:
```bash
start_agent "[NomeAgente]" [PORTA] "server.py" "/caminho/completo/do/agente"
```

### ❌ NUNCA:
```bash
start_agent "[NomeAgente]" [PORTA] "app.py" "/caminho"     # ERRADO!
start_agent "[NomeAgente]" [PORTA] "main.py" "/caminho"    # ERRADO!
```

---

## 📦 Dependências Obrigatórias no pyproject.toml

```toml
[project]
name = "a2a-nome-agente"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "a2a-sdk",  # ✅ OBRIGATÓRIO
    # outras dependências específicas
]

[tool.uv.sources]
a2a-sdk = { path = "../a2a-python" }  # ✅ OBRIGATÓRIO
```

---

## 🎯 Portas Padrão Atuais

| Agente | Porta | Arquivo |
|--------|-------|---------|
| HelloWorld | 9999 | server.py |
| Turso | 4243 | server.py |
| Marvin | 10030 | server.py |

---

## ⚠️ Problemas Comuns e Soluções

### Problema: "Working..." infinito
**Causa**: Usando app.py sem TaskState  
**Solução**: Migrar para server.py com agent_executor.py

### Problema: POST retorna 404
**Causa**: Usando FastAPI simples sem handlers A2A  
**Solução**: Usar A2AStarletteApplication com DefaultRequestHandler

### Problema: Importações não encontradas
**Causa**: Caminhos incorretos ou falta de uv  
**Solução**: 
1. Usar importações relativas para arquivos locais
2. Executar com `uv run python server.py`

### Problema: Agent não inicia
**Causa**: pyproject.toml sem dependências corretas  
**Solução**: Adicionar a2a-sdk nas dependências

---

## ✅ Checklist de Verificação

Antes de considerar um agente pronto:

- [ ] Arquivo `server.py` existe e segue o padrão
- [ ] Arquivo `agent_executor.py` herda de `AgentExecutor`
- [ ] Arquivo `agent.py` implementa a lógica do agente
- [ ] `pyproject.toml` tem `a2a-sdk` como dependência
- [ ] Script de inicialização usa `server.py` (não app.py)
- [ ] Porta definida e não conflita com outros agentes
- [ ] TaskState funciona (working → completed)
- [ ] Discovery endpoint responde em `/.well-known/agent.json`

---

## 🔴 REGRA FUNDAMENTAL

> **TODOS os agentes DEVEM usar server.py no padrão A2A. Sem exceções.**

Este padrão garante:
- ✅ Compatibilidade total com o protocolo A2A
- ✅ TaskState funcionando corretamente
- ✅ Streaming e eventos assíncronos
- ✅ Integração com Claude Flow e outros sistemas A2A
- ✅ Manutenibilidade e consistência do código

---

*Última atualização: 11 de Agosto de 2025*  
*Versão: 1.0.0*