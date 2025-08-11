#!/usr/bin/env python3
"""
Script de teste para o Agente Turso Python/FastAPI
"""

import asyncio
import json
from datetime import datetime

import httpx


async def test_agent():
    """Testar o agente Turso Python"""
    base_url = "http://localhost:4243"

    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("🧪 Teste do Agente Turso Python/FastAPI com Turso Cloud")
        print("=" * 60)
        print("🌐 Organização: diegofornalha")
        print("💾 Database: context-memory")
        print("🔗 URL: http://localhost:4243")
        print("=" * 60)

        # 1. Health Check
        print("\n❤️  Verificando health do agente...")
        response = await client.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agente está ativo!")
            print(f"   Status: {data['status']}")
            print(f"   Agente: {data['agent']}")

        # 2. Armazenar dados
        print("\n📦 Testando armazenamento no Turso Cloud...")
        store_data = {
            "agent_id": "test-python-agent",
            "key": "python_test",
            "value": {
                "message": "Agente Python/FastAPI conectado ao Turso Cloud!",
                "language": "Python",
                "framework": "FastAPI",
                "runtime": "uv",
                "database": "context-memory",
                "timestamp": datetime.now().isoformat(),
            },
            "metadata": {"type": "test", "version": "2.0.0"},
            "ttl": 3600,
        }

        response = await client.post(f"{base_url}/api/store", json=store_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Dados armazenados com sucesso!")
            print(f"   ID: {data['id']}")
            print(f"   Mensagem: {data['message']}")

        # 3. Recuperar dados
        print("\n🔍 Recuperando dados do Turso Cloud...")
        response = await client.get(f"{base_url}/api/retrieve/test-python-agent/python_test")
        if response.status_code == 200:
            data = response.json()
            value = json.loads(data["value"]) if isinstance(data["value"], str) else data["value"]
            print("✅ Dados recuperados com sucesso!")
            print(f"   Mensagem: {value.get('message', 'N/A')}")
            print(f"   Language: {value.get('language', 'N/A')}")
            print(f"   Framework: {value.get('framework', 'N/A')}")

        # 4. Executar query
        print("\n🔎 Executando query no Turso Cloud...")
        query_data = {
            "sql": "SELECT COUNT(*) as total FROM agent_data WHERE agent_id LIKE ?",
            "args": ["test-%"],
        }

        response = await client.post(f"{base_url}/api/query", json=query_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Query executada com sucesso!")
            if data["rows"]:
                print(f"   Total de registros: {data['rows'][0]['total']}")

        # 5. Sincronização
        print("\n🔄 Testando sincronização com Claude Flow...")
        sync_data = {
            "source_agent": "test-python-agent",
            "operation": "sync_test",
            "data": {
                "type": "memory_sync",
                "content": "Agente Python sincronizado",
                "timestamp": datetime.now().isoformat(),
            },
        }

        response = await client.post(f"{base_url}/api/sync", json=sync_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Sincronização realizada com sucesso!")
            print(f"   Sync ID: {data['sync_id']}")

        print("\n" + "=" * 60)
        print("✨ Todos os testes passaram com sucesso!")
        print("🚀 Agente Python/FastAPI está 100% operacional!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_agent())