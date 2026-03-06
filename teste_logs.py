#!/usr/bin/env python3
"""
🧪 Teste rápido dos logs automáticos INFO
Executa a API e mostra que os logs aparecem automaticamente.
"""

import requests
import time
import json
import sys

API_URL = "http://localhost:8000"

def test_logs():
    print("🧪 Teste de Logs Automáticos INFO")
    print("=" * 60)
    print()
    
    # Criar Being
    print("📍 1. Criando Being...")
    response = requests.post(
        f"{API_URL}/beings/",
        json={
            "being_name": "TestBeing",
            "language": "pt",
            "user_id": "test-user-123"
        }
    )
    
    if response.status_code != 200:
        print(f"✗ Erro ao criar Being: {response.status_code}")
        sys.exit(1)
        
    being_data = response.json()
    being_id = being_data["id"]
    print(f"✓ Being criado: {being_id}")
    print()
    
    # Chat
    print("📍 2. Enviando mensagem...")
    response = requests.post(
        f"{API_URL}/beings/{being_id}/chat",
        json={"message": "Olá, você está bem?"}
    )
    
    if response.status_code != 200:
        print(f"✗ Erro no chat: {response.status_code}")
        sys.exit(1)
        
    chat_response = response.json()
    print(f"✓ Resposta: {chat_response['response'][:50]}...")
    print()
    
    # Sleep
    print("📍 3. Iniciando sleep...")
    response = requests.post(
        f"{API_URL}/beings/{being_id}/sleep",
        json={"num_rollouts": 100}
    )
    
    if response.status_code != 200:
        print(f"✗ Erro no sleep: {response.status_code}")
        sys.exit(1)
        
    print("✓ Sleep executado")
    print()
    
    # Wake
    print("📍 4. Despertando Being...")
    response = requests.post(f"{API_URL}/beings/{being_id}/wake")
    
    if response.status_code != 200:
        print(f"✗ Erro no wake: {response.status_code}")
        sys.exit(1)
        
    print("✓ Being despertou")
    print()
    
    # Consolidate
    print("📍 5. Consolidando memória...")
    response = requests.post(f"{API_URL}/beings/{being_id}/consolidate")
    
    if response.status_code != 200:
        print(f"✗ Erro na consolidação: {response.status_code}")
        sys.exit(1)
        
    print("✓ Memória consolidada")
    print()
    
    print("=" * 60)
    print("✅ Teste completo!")
    print()
    print("💡 Durante este teste, você deve ter visto logs INFO no terminal da API")
    print("   mostrando cada operação (criar, chat, sleep, wake, consolidate)")
    print()
    print("📂 Verifique também o arquivo serhu.log na raiz do projeto")

if __name__ == "__main__":
    try:
        test_logs()
    except requests.exceptions.ConnectionError:
        print("✗ Erro: API não está rodando!")
        print()
        print("Execute primeiro em outro terminal:")
        print("  cd packages/api")
        print("  python -m uvicorn serhu_api.app:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏸️ Teste interrompido")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
