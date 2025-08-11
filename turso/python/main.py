#!/usr/bin/env python3
"""
Agente A2A Turso - Gerenciamento de Persistência de Dados
Porta: 4243
Versão: 2.0.0 - Python/FastAPI com uv
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
import libsql_client
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from config import settings
from models import (
    AgentData,
    AgentMetadata,
    BatchOperation,
    HealthResponse,
    QueryRequest,
    StoreRequest,
    StoreResponse,
    SyncRequest,
    SyncResponse,
)

# Configurar logging estruturado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class TursoAgent:
    """Agente A2A para Turso Database"""

    def __init__(self):
        self.agent_id = settings.AGENT_ID
        self.agent_name = settings.AGENT_NAME
        self.port = settings.PORT
        self.turso_client: Optional[libsql_client.Client] = None
        self.metadata = AgentMetadata(
            id=self.agent_id,
            name=self.agent_name,
            type="persistence",
            version="2.0.0",
            capabilities=[
                "data-storage",
                "query-execution",
                "schema-management",
                "sync-memory",
                "batch-operations",
                "real-time-updates",
            ],
            status="initializing",
            port=str(self.port),
            endpoints={
                "health": "/health",
                "discovery": "/discovery",
                "store": "/api/store",
                "retrieve": "/api/retrieve",
                "query": "/api/query",
                "sync": "/api/sync",
                "schema": "/api/schema",
                "batch": "/api/batch",
            },
        )
        self.discovery_task: Optional[asyncio.Task] = None

    async def initialize_turso(self) -> None:
        """Inicializar conexão com Turso"""
        try:
            # Conectar ao Turso Cloud
            self.turso_client = libsql_client.create_client(
                url=settings.TURSO_DATABASE_URL, auth_token=settings.TURSO_AUTH_TOKEN
            )

            # Criar tabelas base
            await self.setup_database()

            self.metadata.status = "active"
            logger.info("turso_connected", database=settings.TURSO_DEFAULT_DATABASE)

        except Exception as e:
            logger.error("turso_connection_error", error=str(e))
            self.metadata.status = "error"
            raise

    async def setup_database(self) -> None:
        """Configurar esquema do banco de dados"""
        queries = [
            # Tabela para armazenamento geral de dados
            """CREATE TABLE IF NOT EXISTS agent_data (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                UNIQUE(agent_id, key)
            )""",
            # Tabela para memória de agentes
            """CREATE TABLE IF NOT EXISTS agent_memory (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                session_id TEXT,
                memory_type TEXT,
                content TEXT NOT NULL,
                embedding TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            # Criar índice separadamente
            "CREATE INDEX IF NOT EXISTS idx_agent_session ON agent_memory (agent_id, session_id)",
            # Tabela para logs de sincronização
            """CREATE TABLE IF NOT EXISTS sync_logs (
                id TEXT PRIMARY KEY,
                source_agent TEXT NOT NULL,
                target_agent TEXT,
                operation TEXT NOT NULL,
                data TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            # Tabela para configurações de PRP
            """CREATE TABLE IF NOT EXISTS prp_configs (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                config_type TEXT NOT NULL,
                config_data TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                active BOOLEAN DEFAULT true,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
        ]

        for query in queries:
            try:
                await self.turso_client.execute(query)
            except Exception as e:
                logger.warning("table_creation_warning", error=str(e))

    async def register_with_discovery(self) -> None:
        """Registrar agente no serviço de discovery"""
        if not settings.A2A_DISCOVERY_URL:
            logger.warning("discovery_not_configured")
            return

        while True:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{settings.A2A_DISCOVERY_URL}/register",
                        json={
                            **self.metadata.model_dump(),
                            "url": f"http://localhost:{self.port}",
                        },
                        timeout=5.0,
                    )
                    if response.status_code == 200:
                        logger.info("discovery_registered")
            except Exception as e:
                logger.error("discovery_registration_error", error=str(e))

            await asyncio.sleep(settings.A2A_DISCOVERY_INTERVAL)

    async def store_data(self, request: StoreRequest) -> StoreResponse:
        """Armazenar dados no Turso"""
        try:
            data_id = str(uuid4())
            expires_at = None

            if request.ttl:
                expires_at = (
                    datetime.now(timezone.utc) + timedelta(seconds=request.ttl)
                ).isoformat()

            await self.turso_client.execute(
                """INSERT OR REPLACE INTO agent_data 
                   (id, agent_id, key, value, metadata, expires_at, updated_at) 
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                [
                    data_id,
                    request.agent_id,
                    request.key,
                    request.value.model_dump_json() if hasattr(request.value, 'model_dump_json') else str(request.value),
                    request.metadata.model_dump_json() if request.metadata else None,
                    expires_at,
                ],
            )

            return StoreResponse(
                success=True, id=data_id, message="Dados armazenados com sucesso"
            )

        except Exception as e:
            logger.error("store_error", error=str(e))
            raise HTTPException(status_code=500, detail="Erro ao armazenar dados")

    async def retrieve_data(self, agent_id: str, key: str) -> Dict[str, Any]:
        """Recuperar dados do Turso"""
        try:
            result = await self.turso_client.execute(
                """SELECT * FROM agent_data 
                   WHERE agent_id = ? AND key = ? 
                   AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)""",
                [agent_id, key],
            )

            if not result.rows:
                raise HTTPException(status_code=404, detail="Dados não encontrados")

            row = result.rows[0]
            return {
                "id": row["id"],
                "agent_id": row["agent_id"],
                "key": row["key"],
                "value": row["value"],
                "metadata": row["metadata"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error("retrieve_error", error=str(e))
            raise HTTPException(status_code=500, detail="Erro ao recuperar dados")

    async def execute_query(self, request: QueryRequest) -> Dict[str, Any]:
        """Executar query customizada"""
        try:
            # Verificar se é uma query SELECT (somente leitura)
            if not request.sql.strip().upper().startswith("SELECT"):
                raise HTTPException(
                    status_code=403, detail="Apenas queries SELECT são permitidas"
                )

            result = await self.turso_client.execute(request.sql, request.args or [])

            return {
                "rows": result.rows,
                "columns": result.columns if hasattr(result, "columns") else [],
                "rowsAffected": result.rows_affected if hasattr(result, "rows_affected") else 0,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error("query_error", error=str(e))
            raise HTTPException(status_code=500, detail="Erro ao executar query")

    async def sync_data(self, request: SyncRequest) -> SyncResponse:
        """Sincronizar com Claude Flow"""
        try:
            sync_id = str(uuid4())

            await self.turso_client.execute(
                """INSERT INTO sync_logs (id, source_agent, operation, data, status) 
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    sync_id,
                    request.source_agent,
                    request.operation,
                    str(request.data),
                    "completed",
                ],
            )

            if settings.CLAUDE_FLOW_SYNC_ENABLED:
                logger.info("claude_flow_sync", sync_id=sync_id)

            return SyncResponse(
                success=True, sync_id=sync_id, message="Sincronização realizada com sucesso"
            )

        except Exception as e:
            logger.error("sync_error", error=str(e))
            raise HTTPException(status_code=500, detail="Erro na sincronização")

    async def batch_operations(self, operations: List[BatchOperation]) -> Dict[str, Any]:
        """Executar operações em lote"""
        try:
            # Execute all operations in a transaction
            async with self.turso_client.transaction():
                for op in operations:
                    await self.turso_client.execute(op.sql, op.args or [])

            return {
                "success": True,
                "count": len(operations),
                "message": "Operações em lote executadas com sucesso",
            }

        except Exception as e:
            logger.error("batch_error", error=str(e))
            raise HTTPException(status_code=500, detail="Erro em operações em lote")

    async def shutdown(self) -> None:
        """Shutdown gracioso do agente"""
        logger.info("shutdown_initiated")
        if self.discovery_task:
            self.discovery_task.cancel()
        if self.turso_client:
            await self.turso_client.close()


# Instância global do agente
agent = TursoAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    # Startup
    await agent.initialize_turso()
    agent.discovery_task = asyncio.create_task(agent.register_with_discovery())
    logger.info(
        "agent_started",
        name=agent.agent_name,
        port=agent.port,
        capabilities=agent.metadata.capabilities,
    )
    yield
    # Shutdown
    await agent.shutdown()


# Criar aplicação FastAPI
app = FastAPI(
    title="Turso A2A Agent",
    description="Agente A2A para gerenciamento de persistência com Turso Database",
    version="2.0.0",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log de todas as requisições"""
    start_time = datetime.now(timezone.utc)
    response = await call_next(request)
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration=duration,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    return response


# Rotas
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status=agent.metadata.status,
        agent=agent.agent_name,
        uptime=0,  # Seria calculado baseado no tempo de início
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/discovery")
async def discovery():
    """Discovery A2A endpoint"""
    return agent.metadata.model_dump()


@app.get("/.well-known/agent.json")
async def agent_json():
    """A2A Agent Card - Well-Known endpoint"""
    return {
        "agent_name": agent.agent_name,
        "project_name": "turso-a2a-agent",
        "version": "2.0.0",
        "description": "Agente A2A para gerenciamento de persistência de dados com Turso Database",
        "role": "Data Persistence Manager",
        "goal": "Fornecer persistência confiável e distribuída de dados para todos os agentes do sistema A2A",
        "backstory": "Especialista em bancos de dados distribuídos com foco em performance, confiabilidade e sincronização de dados entre múltiplos agentes.",
        "id": agent.agent_id,
        "port": agent.port,
        "capabilities": agent.metadata.capabilities,
        "communication": {
            "transport": "http",
            "format": "json",
            "protocols": ["A2A/1.0"]
        },
        "discovery": {
            "auto_register": True,
            "registry_endpoint": settings.A2A_DISCOVERY_URL,
            "heartbeat_interval": settings.A2A_DISCOVERY_INTERVAL
        },
        "endpoints": agent.metadata.endpoints,
        "status": agent.metadata.status,
        "database": {
            "provider": "Turso",
            "organization": settings.TURSO_ORGANIZATION,
            "database": settings.TURSO_DEFAULT_DATABASE,
            "features": [
                "distributed",
                "replicated",
                "edge-computing",
                "sql-compatible",
                "real-time-sync"
            ]
        }
    }


@app.post("/api/store", response_model=StoreResponse)
async def store(request: StoreRequest):
    """Armazenar dados"""
    return await agent.store_data(request)


@app.get("/api/retrieve/{agent_id}/{key}")
async def retrieve(agent_id: str, key: str):
    """Recuperar dados"""
    return await agent.retrieve_data(agent_id, key)


@app.post("/api/query")
async def query(request: QueryRequest):
    """Executar query customizada"""
    return await agent.execute_query(request)


@app.post("/api/sync", response_model=SyncResponse)
async def sync(request: SyncRequest):
    """Sincronizar com Claude Flow"""
    return await agent.sync_data(request)


@app.post("/api/batch")
async def batch(operations: List[BatchOperation]):
    """Operações em lote"""
    return await agent.batch_operations(operations)


@app.post("/api/schema")
async def schema(request: Dict[str, Any]):
    """Gerenciar esquema do banco"""
    try:
        table_name = request.get("table_name")
        columns = request.get("columns", [])

        if not table_name or not columns:
            raise HTTPException(
                status_code=400, detail="table_name e columns são obrigatórios"
            )

        column_defs = ", ".join(
            f"{col['name']} {col['type']} {col.get('constraints', '')}" for col in columns
        )

        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"
        await agent.turso_client.execute(sql)

        return {
            "success": True,
            "message": f"Tabela {table_name} criada/atualizada com sucesso",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("schema_error", error=str(e))
        raise HTTPException(status_code=500, detail="Erro ao gerenciar esquema")


def handle_signal(signum, frame):
    """Tratamento de sinais para shutdown gracioso"""
    logger.info("signal_received", signal=signum)
    sys.exit(0)


def run():
    """Função principal para executar o agente"""
    # Registrar tratadores de sinais
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Executar servidor
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=False,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": settings.LOG_LEVEL,
                "handlers": ["default"],
            },
        },
    )


if __name__ == "__main__":
    run()