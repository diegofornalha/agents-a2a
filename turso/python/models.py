"""
Modelos Pydantic para o Agente Turso
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentMetadata(BaseModel):
    """Metadados do agente A2A"""

    id: str
    name: str
    type: str
    version: str
    capabilities: List[str]
    status: str
    port: str
    endpoints: Dict[str, str]


class StoreRequest(BaseModel):
    """Requisição para armazenar dados"""

    agent_id: str = Field(..., description="ID do agente")
    key: str = Field(..., description="Chave única para os dados")
    value: Any = Field(..., description="Valor a ser armazenado")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados opcionais")
    ttl: Optional[int] = Field(None, description="Time to live em segundos")


class StoreResponse(BaseModel):
    """Resposta do armazenamento"""

    success: bool
    id: str
    message: str


class QueryRequest(BaseModel):
    """Requisição para executar query"""

    sql: str = Field(..., description="Query SQL a ser executada")
    args: Optional[List[Any]] = Field(None, description="Argumentos para a query")


class SyncRequest(BaseModel):
    """Requisição de sincronização"""

    source_agent: str = Field(..., description="Agente de origem")
    operation: str = Field(..., description="Tipo de operação")
    data: Dict[str, Any] = Field(..., description="Dados para sincronizar")
    target_agent: Optional[str] = Field(None, description="Agente de destino")


class SyncResponse(BaseModel):
    """Resposta de sincronização"""

    success: bool
    sync_id: str
    message: str


class BatchOperation(BaseModel):
    """Operação em lote"""

    sql: str = Field(..., description="Query SQL")
    args: Optional[List[Any]] = Field(None, description="Argumentos")


class HealthResponse(BaseModel):
    """Resposta do health check"""

    status: str
    agent: str
    uptime: float
    timestamp: str


class AgentData(BaseModel):
    """Modelo de dados do agente"""

    id: str
    agent_id: str
    key: str
    value: Any
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class AgentMemory(BaseModel):
    """Modelo de memória do agente"""

    id: str
    agent_id: str
    session_id: Optional[str] = None
    memory_type: Optional[str] = None
    content: str
    embedding: Optional[str] = None
    created_at: datetime


class SyncLog(BaseModel):
    """Log de sincronização"""

    id: str
    source_agent: str
    target_agent: Optional[str] = None
    operation: str
    data: Optional[str] = None
    status: str
    created_at: datetime


class PRPConfig(BaseModel):
    """Configuração PRP"""

    id: str
    agent_id: str
    config_type: str
    config_data: str
    version: int = 1
    active: bool = True
    created_at: datetime
    updated_at: datetime


class SchemaRequest(BaseModel):
    """Requisição para criar/atualizar esquema"""

    table_name: str = Field(..., description="Nome da tabela")
    columns: List[Dict[str, str]] = Field(..., description="Definição das colunas")