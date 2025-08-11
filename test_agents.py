#!/usr/bin/env python3
"""
Script de teste para verificar os agentes A2A
"""

import requests
import json
import time

def test_agent(name, port, test_message):
    """Testa um agente A2A"""
    print(f"\n🧪 Testando {name} na porta {port}...")
    
    # Testar discovery
    try:
        response = requests.get(f"http://localhost:{port}/.well-known/agent.json")
        if response.status_code == 200:
            agent_card = response.json()
            print(f"✅ Discovery OK - Agent: {agent_card.get('name')}")
        else:
            print(f"❌ Discovery falhou: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    # Testar POST com mensagem A2A
    url = f"http://localhost:{port}/"
    headers = {"Content-Type": "application/json"}
    
    # Payload A2A padrão
    payload = {
        "message": {
            "type": "user_text",
            "text": test_message,
            "contextId": f"test-context-{int(time.time())}",
            "messageId": f"msg-{int(time.time())}"
        }
    }
    
    try:
        print(f"📤 Enviando: {test_message}")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Resposta recebida (200 OK)")
            
            # Tentar parsear a resposta
            try:
                result = response.json()
                print(f"📊 Tipo de resposta: {type(result)}")
                if isinstance(result, dict):
                    if 'status' in result:
                        print(f"   Status: {result.get('status')}")
                    if 'message' in result:
                        print(f"   Mensagem: {result.get('message')}")
            except:
                print(f"   Resposta (texto): {response.text[:200]}")
        else:
            print(f"❌ Erro na resposta: {response.status_code}")
            print(f"   Detalhes: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")


def main():
    print("🚀 Iniciando testes dos agentes A2A...")
    print("=" * 50)
    
    # Testar HelloWorld
    test_agent("HelloWorld", 9999, "hello")
    
    # Testar Turso
    test_agent("Turso", 4243, "help")
    
    # Testar Marvin
    test_agent("Marvin", 10030, "My name is John Doe, email: john@example.com")
    
    print("\n" + "=" * 50)
    print("✅ Testes concluídos!")


if __name__ == "__main__":
    main()