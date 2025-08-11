"""
Configurações do Agente Turso
"""

import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Configuração básica
    PORT: int = 4243
    AGENT_NAME: str = "TursoAgent"
    AGENT_ID: str = "turso-agent-001"

    # Turso Database
    TURSO_ORGANIZATION: str = "diegofornalha"
    TURSO_DEFAULT_DATABASE: str = "context-memory"
    TURSO_DATABASE_URL: str = "libsql://context-memory-diegofornalha.aws-us-east-1.turso.io"
    TURSO_AUTH_TOKEN: str = ""

    # A2A Discovery
    A2A_DISCOVERY_URL: str = "http://localhost:4240"
    A2A_DISCOVERY_INTERVAL: int = 30

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:4241",
        "http://localhost:4242",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/turso-agent.log"

    # Cache
    CACHE_TTL: int = 3600
    CACHE_CHECK_PERIOD: int = 600

    # Performance
    MAX_CONNECTIONS: int = 100
    CONNECTION_TIMEOUT: int = 30
    QUERY_TIMEOUT: int = 10

    # Claude Flow
    CLAUDE_FLOW_SYNC_ENABLED: bool = True
    CLAUDE_FLOW_SYNC_INTERVAL: int = 10

    # Segurança
    JWT_SECRET: str = "turso-secret-key-2024"
    API_KEY: str = "turso-api-key-2024"
    
    # OpenAI (opcional)
    OPENAI_API_KEY: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse CORS_ORIGINS se vier como string JSON
        if isinstance(self.CORS_ORIGINS, str):
            try:
                self.CORS_ORIGINS = json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                self.CORS_ORIGINS = self.CORS_ORIGINS.split(",")


# Instância global das configurações
settings = Settings()