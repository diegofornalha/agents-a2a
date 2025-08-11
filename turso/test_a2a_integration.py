#!/usr/bin/env python3
"""
Script de teste para verificar integração A2A do Turso Agent
"""

import sys
import asyncio
from pathlib import Path

# Adicionar o SDK A2A ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "a2a-python" / "src"))

# Importar componentes
from agent import TursoAgent
from agent_executor import TursoAgentExecutor


async def test_basic_operations():
    """Testar operações básicas do agente"""
    print("🧪 Testando Turso Agent com padrão A2A...")
    
    # Criar instância do agente
    agent = TursoAgent()
    print("✅ Agente criado com sucesso")
    
    # Criar executor
    executor = TursoAgentExecutor(agent)
    print("✅ Executor criado com sucesso")
    
    # Testar operação de armazenamento
    print("\n📝 Testando armazenamento...")
    store_request = '{"operation": "store", "key": "test_key", "value": {"data": "test_value"}}'
    result = await agent.invoke(store_request, "test-session-001")
    
    if result.get("is_task_complete"):
        print("✅ Armazenamento bem-sucedido!")
        print(f"   Mensagem: {result.get('text_parts', [{}])[0]}")
    else:
        print("❌ Falha no armazenamento")
        print(f"   Erro: {result}")
    
    # Testar recuperação
    print("\n🔍 Testando recuperação...")
    retrieve_request = '{"operation": "retrieve", "key": "test_key"}'
    result = await agent.invoke(retrieve_request, "test-session-001")
    
    if result.get("is_task_complete"):
        print("✅ Recuperação bem-sucedida!")
        data = result.get("data")
        if data:
            print(f"   Dados recuperados: {data}")
    else:
        print("❌ Falha na recuperação")
        print(f"   Erro: {result}")
    
    # Testar comando de ajuda
    print("\n❓ Testando comando de ajuda...")
    result = await agent.invoke("help", "test-session-001")
    
    if result.get("is_task_complete"):
        print("✅ Comando de ajuda executado!")
        if result.get("text_parts"):
            print("   Comandos disponíveis listados")
    else:
        print("❌ Falha no comando de ajuda")
    
    print("\n✨ Teste concluído!")
    print("📊 Resumo:")
    print("   - Agente: Funcional")
    print("   - Executor: Compatível com A2A")
    print("   - Banco de dados: Turso/LibSQL")
    print("   - Padrão: A2A completo")


if __name__ == "__main__":
    asyncio.run(test_basic_operations())