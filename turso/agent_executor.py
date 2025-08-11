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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TursoAgentExecutor(AgentExecutor):
    """
    Turso Database agent executor following A2A pattern.
    """

    def __init__(self, agent):
        self.agent = agent

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        # Processar a query com o agente Turso
        try:
            result = await self.agent.invoke(query, task.contextId)
            
            # Extrair informações do resultado
            is_task_complete = result.get("is_task_complete", False)
            require_user_input = result.get("require_user_input", False)
            text_parts = result.get("text_parts", [])
            data = result.get("data", {})
            
            logger.info(
                f"Turso result: complete={is_task_complete}, require_input={require_user_input}, "
                f"has_data={bool(data)}, text_parts_len={len(text_parts)}"
            )
            
            # Converter text_parts para string
            text_content = ""
            if text_parts:
                if isinstance(text_parts, list):
                    text_content = "\n".join([
                        part.text if hasattr(part, 'text') else str(part) 
                        for part in text_parts
                    ])
                else:
                    text_content = str(text_parts)
            
            # Criar artefato apropriado
            if data:
                artifact = new_data_artifact(
                    name="turso_result",
                    description="Result from Turso database operation",
                    data=data,
                )
            else:
                artifact = new_text_artifact(
                    name="turso_result",
                    description="Result from Turso database operation",
                    text=text_content or "Operation completed successfully",
                )
            
            # Enviar eventos baseados no estado
            if require_user_input:
                # Requer input do usuário
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.input_required,
                            message=new_agent_text_message(
                                text_content or "Please provide additional information",
                                task.contextId,
                                task.id,
                            ),
                        ),
                        final=True,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )
            elif is_task_complete:
                # Tarefa completa
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        append=False,
                        contextId=task.contextId,
                        taskId=task.id,
                        lastChunk=True,
                        artifact=artifact,
                    )
                )
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(state=TaskState.completed),
                        final=True,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )
            else:
                # Ainda processando
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.working,
                            message=new_agent_text_message(
                                "Processing database operation...",
                                task.contextId,
                                task.id,
                            ),
                        ),
                        final=False,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )
                
        except Exception as e:
            logger.error(f"Error executing Turso agent: {str(e)}")
            # Enviar evento de erro
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=new_agent_text_message(
                            f"Error: {str(e)}",
                            task.contextId,
                            task.id,
                        ),
                    ),
                    final=True,
                    contextId=task.contextId,
                    taskId=task.id,
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel operation - not supported for database operations"""
        raise Exception("Cancel not supported for database operations")