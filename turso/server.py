#!/usr/bin/env python3
"""
Servidor A2A para o Turso Agent
Porta: 4243
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

from agent import TursoAgent
from agent_executor import TursoAgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill


def get_agent_card(host: str, port: int) -> AgentCard:
    """Retorna o Agent Card para o TursoAgent seguindo padrão A2A"""
    
    capabilities = AgentCapabilities(
        streaming=True,
        batch=True,
        persistence=True
    )
    
    skills = [
        AgentSkill(
            id="store_data",
            name="Armazenar Dados",
            description="Armazena dados de forma persistente com suporte a TTL",
            tags=["storage", "persistence", "database", "turso"],
            examples=[
                '{"operation": "store", "key": "user_123", "value": {"name": "João", "email": "joao@example.com"}}',
                "store campaign_data {'status': 'active', 'budget': 5000}",
                "salvar configurações do agente"
            ],
        ),
        AgentSkill(
            id="retrieve_data",
            name="Recuperar Dados",
            description="Recupera dados armazenados por chave",
            tags=["query", "fetch", "database", "turso"],
            examples=[
                '{"operation": "retrieve", "key": "user_123"}',
                "get campaign_data",
                "buscar configurações"
            ],
        ),
        AgentSkill(
            id="execute_query",
            name="Executar Query SQL",
            description="Executa queries SQL customizadas (apenas SELECT)",
            tags=["sql", "query", "database", "analytics"],
            examples=[
                '{"operation": "query", "sql": "SELECT * FROM agent_data WHERE agent_id = ?"}',
                "listar todas as chaves",
                "contar registros expirados"
            ],
        ),
        AgentSkill(
            id="memory_sync",
            name="Sincronizar Memória",
            description="Sincroniza memória com outros agentes e Claude Flow",
            tags=["sync", "memory", "coordination", "claude-flow"],
            examples=[
                "sincronizar memória do agente",
                "compartilhar contexto entre agentes",
                "persistir estado do workflow"
            ],
        ),
        AgentSkill(
            id="batch_operations",
            name="Operações em Lote",
            description="Executa múltiplas operações de forma otimizada",
            tags=["batch", "performance", "optimization"],
            examples=[
                "processar lista de dados",
                "importar múltiplos registros",
                "atualizar várias chaves"
            ],
        )
    ]
    
    return AgentCard(
        name="Turso Persistence Agent",
        description="Agente A2A para persistência de dados usando Turso Database com suporte a SQL, TTL e sincronização",
        url=f"http://{host}:{port}/",
        version="2.0.0",
        defaultInputModes=["text", "text/plain", "application/json"],
        defaultOutputModes=["text", "text/plain", "application/json"],
        capabilities=capabilities,
        skills=skills,
        metadata={
            "database": "Turso/LibSQL",
            "supports_ttl": True,
            "supports_sql": True,
            "supports_sync": True,
            "max_storage": "unlimited",
            "persistence": "durable"
        }
    )


def main():
    """Iniciar o servidor Turso Agent no padrão A2A"""
    
    # Configurações
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 4243))
    
    print(f"🚀 Iniciando Turso Agent (A2A) em {host}:{port}...")
    print(f"📦 Usando padrão A2A com SDK oficial")
    
    # Criar o agente
    agent = TursoAgent()
    
    # Criar o executor do agente
    agent_executor = TursoAgentExecutor(agent=agent)
    
    # Criar o handler de requisições A2A
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )
    
    # Criar o servidor A2A
    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port),
        http_handler=request_handler
    )
    
    print("✅ Servidor configurado com padrão A2A")
    print("🗄️  Turso Database conectado")
    print("🔄 Suporte a streaming habilitado")
    print("💾 Persistência durável ativa")
    
    # Iniciar o servidor
    uvicorn.run(
        server.build(),
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()