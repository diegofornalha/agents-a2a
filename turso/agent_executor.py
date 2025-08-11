import asyncio
import json
import logging
from collections.abc import AsyncIterable
from typing import Any

from a2a.agent_executor import AgentExecutor

from .agent import TursoAgent

logger = logging.getLogger(__name__)


class TursoAgentExecutor(AgentExecutor):
    """Executor para o TursoAgent seguindo padrão A2A"""

    def __init__(self, agent: TursoAgent):
        self.agent = agent

    def can_handle(self, content: Any) -> bool:
        """Verifica se pode processar o conteúdo
        
        Args:
            content: Conteúdo a ser verificado
            
        Returns:
            True se pode processar o conteúdo
        """
        # Aceita strings (comandos ou JSON) e dicionários
        if isinstance(content, str):
            return True
        
        if isinstance(content, dict):
            # Verifica se tem estrutura esperada
            return any(key in content for key in ["operation", "key", "value", "sql"])
        
        return False

    async def invoke(self, content: Any, session_id: str) -> dict[str, Any]:
        """Invoca o agente para processar o conteúdo
        
        Args:
            content: Conteúdo a ser processado
            session_id: ID da sessão
            
        Returns:
            Resultado do processamento
        """
        try:
            # Converter dicionário para JSON string se necessário
            if isinstance(content, dict):
                content = json.dumps(content)
            elif not isinstance(content, str):
                content = str(content)
            
            # Chamar o agente
            result = await self.agent.invoke(content, session_id)
            
            # Log do resultado
            logger.info(
                f"[Session {session_id}] Processamento concluído. "
                f"Task complete: {result.get('is_task_complete', False)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no executor para sessão {session_id}: {e}")
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "text_parts": [
                    {"type": "text", "text": f"❌ Erro no processamento: {str(e)}"}
                ],
                "data": None
            }

    async def stream(
        self, content: Any, session_id: str
    ) -> AsyncIterable[dict[str, Any]]:
        """Stream de respostas do agente
        
        Args:
            content: Conteúdo a ser processado
            session_id: ID da sessão
            
        Yields:
            Partes da resposta em stream
        """
        try:
            # Converter para string se necessário
            if isinstance(content, dict):
                content = json.dumps(content)
            elif not isinstance(content, str):
                content = str(content)
            
            # Usar o stream do agente
            async for chunk in self.agent.stream(content, session_id):
                yield chunk
                
        except Exception as e:
            logger.error(f"Erro no stream para sessão {session_id}: {e}")
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"❌ Erro no stream: {str(e)}"
            }