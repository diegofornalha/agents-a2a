import logging
import os
import json
import uuid
import threading
from collections.abc import AsyncIterable
from typing import Annotated, Any, ClassVar, Optional, Dict, List
from datetime import datetime, timedelta

from a2a.types import TextPart
from pydantic import BaseModel, Field
import libsql_experimental as libsql

logger = logging.getLogger(__name__)

# Configuração do banco de dados
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "file:local.db")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")


def _to_text_part(text: str) -> TextPart:
    return TextPart(type="text", text=text)


class StorageRequest(BaseModel):
    """Requisição para armazenar dados"""
    key: str = Field(description="Chave única para o dado")
    value: Any = Field(description="Valor a ser armazenado")
    ttl: Optional[int] = Field(None, description="Tempo de vida em segundos")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais")


class QueryRequest(BaseModel):
    """Requisição para consultar dados"""
    sql: Optional[str] = Field(None, description="Query SQL customizada")
    key: Optional[str] = Field(None, description="Chave para buscar")
    pattern: Optional[str] = Field(None, description="Padrão para buscar múltiplas chaves")


class StorageOutcome(BaseModel):
    """Resultado de uma operação de armazenamento"""
    success: bool
    message: str
    data_id: Optional[str] = None
    stored_data: Optional[Dict[str, Any]] = None


class QueryOutcome(BaseModel):
    """Resultado de uma consulta"""
    success: bool
    data: Optional[Any] = None
    count: int = 0
    message: str


class TursoAgent:
    """Agente de persistência usando Turso Database seguindo padrão A2A"""

    SUPPORTED_CONTENT_TYPES: ClassVar[list[str]] = [
        "text",
        "text/plain",
        "application/json",
    ]

    def __init__(self):
        self.db_client = self._init_database()
        self.agent_id = os.getenv("AGENT_ID", f"turso-agent-{uuid.uuid4()}")

    def _init_database(self):
        """Inicializar conexão com Turso"""
        try:
            if TURSO_DATABASE_URL == "file:local.db" or not TURSO_AUTH_TOKEN:
                logger.info("Usando Turso local (SQLite)")
                client = libsql.connect("local.db")
            else:
                client = libsql.connect(
                    "local.db",
                    sync_url=TURSO_DATABASE_URL,
                    auth_token=TURSO_AUTH_TOKEN
                )
            
            # Criar tabelas necessárias
            self._create_tables(client)
            return client
            
        except Exception as e:
            logger.error(f"Erro ao conectar com Turso: {e}")
            raise

    def _create_tables(self, client):
        """Criar tabelas do banco de dados"""
        queries = [
            """CREATE TABLE IF NOT EXISTS agent_data (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                session_id TEXT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                UNIQUE(agent_id, key)
            )""",
            
            """CREATE TABLE IF NOT EXISTS agent_memory (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                session_id TEXT,
                memory_type TEXT,
                content TEXT NOT NULL,
                embedding TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE INDEX IF NOT EXISTS idx_agent_key ON agent_data(agent_id, key)""",
            """CREATE INDEX IF NOT EXISTS idx_session ON agent_data(session_id)""",
            """CREATE INDEX IF NOT EXISTS idx_expires ON agent_data(expires_at)"""
        ]
        
        for query in queries:
            client.execute(query)
        client.commit()

    async def invoke(self, query: str, sessionId: str) -> dict[str, Any]:
        """Processar uma requisição seguindo padrão A2A
        
        Args:
            query: Entrada do usuário ou comando JSON
            sessionId: Identificador da sessão
            
        Returns:
            Dicionário com resultado da operação
        """
        try:
            logger.debug(
                f"[Session: {sessionId}] PID: {os.getpid()} | "
                f"PyThread: {threading.get_ident()} | Processing: {query[:100]}"
            )
            
            # Tentar parsear como JSON primeiro
            try:
                request_data = json.loads(query)
                operation = request_data.get("operation", "store")
                
                if operation == "store":
                    result = await self._handle_store(request_data, sessionId)
                elif operation == "retrieve":
                    result = await self._handle_retrieve(request_data, sessionId)
                elif operation == "query":
                    result = await self._handle_query(request_data, sessionId)
                else:
                    result = await self._handle_text_command(query, sessionId)
                    
            except json.JSONDecodeError:
                # Tratar como comando de texto
                result = await self._handle_text_command(query, sessionId)
            
            return result
            
        except Exception as e:
            logger.exception(f"Erro ao processar requisição para sessão {sessionId}")
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "text_parts": [
                    _to_text_part(f"Erro ao processar requisição: {str(e)}")
                ],
                "data": None,
            }

    async def _handle_store(self, request_data: dict, sessionId: str) -> dict:
        """Armazenar dados no Turso"""
        try:
            data_id = str(uuid.uuid4())
            key = request_data.get("key")
            value = request_data.get("value")
            ttl = request_data.get("ttl")
            metadata = request_data.get("metadata", {})
            
            expires_at = None
            if ttl:
                expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()
            
            self.db_client.execute(
                """INSERT OR REPLACE INTO agent_data 
                   (id, agent_id, session_id, key, value, metadata, expires_at, updated_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                [
                    data_id,
                    self.agent_id,
                    sessionId,
                    key,
                    json.dumps(value),
                    json.dumps(metadata),
                    expires_at
                ]
            )
            self.db_client.commit()
            
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "text_parts": [
                    _to_text_part(f"✅ Dados armazenados com sucesso! ID: {data_id}, Chave: {key}")
                ],
                "data": {
                    "id": data_id,
                    "key": key,
                    "stored": True
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao armazenar dados: {e}")
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "text_parts": [_to_text_part(f"❌ Erro ao armazenar: {str(e)}")],
                "data": None
            }

    async def _handle_retrieve(self, request_data: dict, sessionId: str) -> dict:
        """Recuperar dados do Turso"""
        try:
            key = request_data.get("key")
            
            result = self.db_client.execute(
                """SELECT * FROM agent_data 
                   WHERE agent_id = ? AND key = ? 
                   AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                   ORDER BY updated_at DESC LIMIT 1""",
                [self.agent_id, key]
            )
            
            rows = result.fetchall()
            if not rows:
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "text_parts": [_to_text_part(f"⚠️ Nenhum dado encontrado para a chave: {key}")],
                    "data": None
                }
            
            row = rows[0]
            data = {
                "id": row[0],
                "key": row[3],
                "value": json.loads(row[4]),
                "metadata": json.loads(row[5]) if row[5] else None,
                "created_at": row[6],
                "updated_at": row[7]
            }
            
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "text_parts": [
                    _to_text_part(f"✅ Dados recuperados para chave: {key}")
                ],
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Erro ao recuperar dados: {e}")
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "text_parts": [_to_text_part(f"❌ Erro ao recuperar: {str(e)}")],
                "data": None
            }

    async def _handle_query(self, request_data: dict, sessionId: str) -> dict:
        """Executar query customizada"""
        try:
            sql = request_data.get("sql")
            
            # Validação de segurança básica
            if sql and not sql.strip().upper().startswith("SELECT"):
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "text_parts": [_to_text_part("⚠️ Apenas queries SELECT são permitidas")],
                    "data": None
                }
            
            result = self.db_client.execute(sql, [])
            rows = result.fetchall()
            
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "text_parts": [
                    _to_text_part(f"✅ Query executada. {len(rows)} registros encontrados.")
                ],
                "data": {
                    "rows": rows,
                    "count": len(rows)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "text_parts": [_to_text_part(f"❌ Erro na query: {str(e)}")],
                "data": None
            }

    async def _handle_text_command(self, query: str, sessionId: str) -> dict:
        """Processar comandos em texto natural"""
        query_lower = query.lower()
        
        # Comandos de ajuda
        if any(word in query_lower for word in ["help", "ajuda", "comandos"]):
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "text_parts": [
                    _to_text_part(
                        "🤖 Turso Agent - Comandos disponíveis:\n\n"
                        "• store <key> <value> - Armazenar dados\n"
                        "• get <key> - Recuperar dados\n"
                        "• list - Listar todas as chaves\n"
                        "• delete <key> - Deletar dados\n"
                        "• stats - Estatísticas do banco\n\n"
                        "Ou envie JSON com operation: store/retrieve/query"
                    )
                ],
                "data": None
            }
        
        # Comando list
        if query_lower.startswith("list"):
            result = self.db_client.execute(
                "SELECT key, updated_at FROM agent_data WHERE agent_id = ? ORDER BY updated_at DESC",
                [self.agent_id]
            )
            rows = result.fetchall()
            
            if rows:
                keys_list = "\n".join([f"• {row[0]} (atualizado: {row[1]})" for row in rows])
                message = f"📋 Chaves armazenadas:\n{keys_list}"
            else:
                message = "📋 Nenhuma chave armazenada ainda"
            
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "text_parts": [_to_text_part(message)],
                "data": {"keys": [row[0] for row in rows]}
            }
        
        # Comando stats
        if query_lower.startswith("stats"):
            result = self.db_client.execute(
                "SELECT COUNT(*) as total, COUNT(DISTINCT key) as unique_keys FROM agent_data WHERE agent_id = ?",
                [self.agent_id]
            )
            row = result.fetchone()
            
            message = f"📊 Estatísticas:\n• Total de registros: {row[0]}\n• Chaves únicas: {row[1]}"
            
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "text_parts": [_to_text_part(message)],
                "data": {"total": row[0], "unique_keys": row[1]}
            }
        
        # Outros comandos
        return {
            "is_task_complete": False,
            "require_user_input": True,
            "text_parts": [
                _to_text_part(
                    "🤔 Não entendi o comando. Digite 'help' para ver os comandos disponíveis."
                )
            ],
            "data": None
        }

    async def stream(self, query: str, sessionId: str) -> AsyncIterable[dict[str, Any]]:
        """Stream de respostas para o padrão A2A
        
        Args:
            query: Entrada do usuário
            sessionId: Identificador da sessão
            
        Returns:
            Stream assíncrono de respostas
        """
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "🔄 Processando sua requisição no Turso Database...",
        }
        
        yield await self.invoke(query, sessionId)