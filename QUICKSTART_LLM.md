# Quick Start: LLM no SerHu 🚀

Execute seu primeiro Ser com GPT-5.4 em 5 minutos.

## 1. Variáveis de Ambiente

```bash
# Copie e edite o arquivo .env
cp .env.example .env

# Adicione sua chave OpenAI (obtém em https://platform.openai.com/account/api-keys)
# OPENAI_API_KEY=sk-...
```

## 2. Instalar Dependências

```bash
cd packages/orchestrator
pip install -e ".[dev]"
```

## 3. Executar Exemplo

```bash
cd /repo/root
python exemplo_uso.py
```

### Esperado:

```
🚀 Inicializando cliente OpenAI (GPT-5.4)...
✅ LLM client inicializado!

🌟 Criando um novo Ser com suporte a LLM...
✅ Ser criado! ID: abc123

💬 Conversando com o Ser via LLM...
👤 Usuário: Olá! Me fale sobre você...
✨ Ser: [resposta automática gerada pelo GPT-5.4]

✨ Exemplo concluído!
```

## 4. Uso Custom

```python
from serhu_orchestrator.orchestrator import Orchestrator
from serhu_orchestrator.llm.openai_client import OpenAIClient
import os
from dotenv import load_dotenv

load_dotenv()

# Cliente LLM
llm = OpenAIClient(api_key=os.environ["OPENAI_API_KEY"])

# Orchestrator com LLM
orch = Orchestrator(
    qdrant_url=os.environ["QDRANT_URL"],
    qdrant_api_key=os.environ["QDRANT_API_KEY"],
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_key=os.environ["SUPABASE_KEY"],
    being_name="Luna",
    language="pt",
    llm_client=llm,
)

# Chat automático!
response, context = orch.chat("Olá, tudo bem?")
print(response)
```

## 📚 Próximos Passos

- Leia [LLM_SETUP.md](./LLM_SETUP.md) para configuração detalhada
- Execute testes: `pytest packages/orchestrator/tests/unit/test_llm_integration.py -v`
- Veja [exemplo_uso.py](./exemplo_uso.py) para exemplo completo

## 🆘 Erros Comuns

| Erro | Solução |
|------|---------|
| `OPENAI_API_KEY not found` | Verifique se `.env` existe e tem a chave |
| `Invalid API key` | Revalide em https://platform.openai.com/account/api-keys |
| `API Rate Limited` | Aguarde alguns minutos ou implemente retry |

## ✅ Você está pronto! 

Seu Ser agora pode aprender e evoluir com GPT-5.4! 🎉
