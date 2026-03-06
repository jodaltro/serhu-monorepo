# Configuração da LLM (GPT-5.4) no SerHu

Este documento descreve como configurar e usar a integração com OpenAI GPT-5.4 no Orchestrator.

## 📋 Pré-requisitos

- Conta OpenAI ativa
- Chave de API OpenAI válida
- Variáveis de ambiente Qdrant e Supabase já configuradas

## 🔑 Configuração das Variáveis de Ambiente

### 1. Obter sua Chave de API OpenAI

1. Acesse: https://platform.openai.com/account/api-keys
2. Crie uma nova chave de API
3. Copie a chave (**NUNCA** compartilhe ou commite)

### 2. Adicionar ao `.env`

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env e adicionar:
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-5.4
```

### 3. Arquivo `.env` Completo

```dotenv
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# OpenAI LLM (NOVO)
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-5.4
```

## 🚀 Uso no Código

### Opção A: Com LLM (Recomendado)

```python
import os
from dotenv import load_dotenv
from serhu_orchestrator.orchestrator import Orchestrator
from serhu_orchestrator.llm.openai_client import OpenAIClient

load_dotenv()

# 1. Criar cliente LLM
llm = OpenAIClient(
    api_key=os.environ["OPENAI_API_KEY"],
    model=os.environ.get("OPENAI_MODEL", "gpt-5.4"),
)

# 2. Inicializar Orchestrator com LLM
orch = Orchestrator(
    qdrant_url=os.environ["QDRANT_URL"],
    qdrant_api_key=os.environ["QDRANT_API_KEY"],
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_key=os.environ["SUPABASE_KEY"],
    being_name="Luna",
    language="pt",
    llm_client=llm,  # ← LLM integrado!
)

# 3. Usar chat() - automático!
response, context = orch.chat(
    "Olá! Me fale sobre você.",
    auto_traits=True  # Extrai traços automaticamente
)
print(response)
```

### Opção B: Sem LLM (Fallback)

```python
# Sem llm_client
orch = Orchestrator(
    qdrant_url=...,
    qdrant_api_key=...,
    supabase_url=...,
    supabase_key=...,
    being_name="Luna",
    # Sem llm_client!
)

# Usa process_message() apenas
ctx = orch.process_message("user", "Olá!")
```

## 🎯 O que a LLM Faz

### Durante a Vigília (Wakefulness)

**`orch.chat(user_message)`** - 4 passos automáticos:

1. **Processa a mensagem do usuário** na memória
2. **Constrói system prompt** com personalidade do Ser
   - HEXACO 24 facetas
   - TCI-R temperamento/caráter
   - Schwartz valores
   - Piaget estágio cognitivo
   - Erikson conflito psicossocial
3. **Envia para GPT-5.4** e gera resposta do Ser
4. **Extrai traços** automaticamente da conversa
   - Deltas clamped entre -0.05 e +0.05
   - Atualiza personalidade em tempo real

### Durante o Sono (Sleep)

**`orch.sleep(num_rollouts=1000)`** - 2 fases enriquecidas:

1. **Semantização (LLM)**
   - GPT-5.4 analisa episódios recentes
   - Extrai fatos semânticos contextuais (vs. rule-based)
   - Se falhar: fallback automático para rule-based

2. **Derivação de Crenças (LLM)**
   - GPT-5.4 atua como "Observador Junguiano"
   - Avalia hipóteses AIXI
   - Define quais padrões viram crenças permanentes
   - Se falhar: fallback para rule-based

## 📊 Comparação

| Recurso | Sem LLM | Com LLM |
|---------|---------|---------|
| `process_message()` | ✅ Manual | ✅ Fun(s)iona |
| `chat()` | ❌ Não disponível | ✅ Automático |
| Extração de traços | ❌ Manual | ✅ Automático |
| Semantização (sleep) | Rule-based | **GPT-5.4** |
| Crenças (sleep) | Rule-based | **GPT-5.4** |
| Latência | Rápido | ~1-3s por turn |

## ⚠️ Tratamento de Erros

Todas as chamadas LLM têm **fallback automático**:

```python
# Se OpenAI API falhar → continua com rule-based
response, context = orch.chat(user_message)

# Se não houver llm_client → erro claro
if not hasattr(orch, '_llm') or orch._llm is None:
    raise RuntimeError(
        "chat() requires an LLM client. "
        "Pass llm_client=OpenAIClient(...) to Orchestrator."
    )
```

## 💰 Custos

### Preços OpenAI (aproximado)

- **Input**: $0.50 / 1M tokens
- **Output**: $1.50 / 1M tokens
- **Típico por turn**: ~0.001 - 0.01 USD

### Estimativa

```
100 turns/dia × 30 dias = 3,000 turns/mês
3,000 × $0.005 (médio) ≈ $15/mês
```

Monitor seu uso em: https://platform.openai.com/account/usage

## 🧪 Testar a Integração

```bash
# Executar exemplo com LLM
python exemplo_uso.py

# Testes unitários
python -m pytest packages/orchestrator/tests/unit/test_llm_integration.py -v

# Testes de integração
python -m pytest packages/orchestrator/tests/integration -v -m integration
```

## 🐛 Troubleshooting

### Erro: "OPENAI_API_KEY not found"

```bash
# Verifique se .env existe
ls -la .env

# Verifique a chave
grep OPENAI_API_KEY .env

# Recarregue o shell
source .env  # ou execute Python novamente
```

### Erro: "Invalid API key"

```bash
# Revalide sua chave em:
https://platform.openai.com/account/api-keys

# Certificar que está usando 'sk-' prefix
# Não funciona: '123abc'
# Funciona: 'sk-proj-...'
```

### Erro: "API Rate Limited"

```python
# Implementar retry com backoff
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def chat_with_retry(orch, message):
    return orch.chat(message)

response, _ = chat_with_retry(orch, "Olá!")
```

## � Notas Técnicas (GPT-5.4)

### Mudanças na API OpenAI

⚠️ **Importante**: GPT-5.4 mudou o parâmetro de controle de tokens:

- ❌ **Anterior**: `max_tokens` (GPT-3.5, GPT-4)
- ✅ **Atual**: `max_completion_tokens` (GPT-5.4+)

O `OpenAIClient` já usa automaticamente `max_completion_tokens`. Se você estiver usando a API OpenAI diretamente, certifique-se de usar o parâmetro correto:

```python
# ❌ NÃO funciona com GPT-5.4
response = client.chat.completions.create(
    model="gpt-5.4",
    messages=[...],
    max_tokens=1024  # ← Erro 400!
)

# ✅ Funciona com GPT-5.4
response = client.chat.completions.create(
    model="gpt-5.4",
    messages=[...],
    max_completion_tokens=1024  # ← Correto!
)
```

### Valores Padrão

| Operação | `max_completion_tokens` | `temperature` |
|----------|------------------------|---------------|
| `chat()` | 1024 | 0.7 |
| `analyze_traits()` | 512 | 0.2 |
| `extract_semantic_facts()` | 512 | 0.3 |
| `derive_beliefs()` | 256 | 0.4 |

## �📚 Referências

- [OpenAI API Docs](https://platform.openai.com/docs/api-reference/chat)
- [GPT-5.4 Announcement](https://openai.com/index/introducing-gpt-5/)
- [Persona Vectors (Anthropic)](https://www.anthropic.com/research/persona-vectors)
- [exemplo_uso.py](./exemplo_uso.py) - Exemplo completo

## ✅ Checklist de Configuração

- [ ] Conta OpenAI criada
- [ ] Chave de API gerada
- [ ] Adicionada ao `.env`
- [ ] Variáveis Qdrant/Supabase configuradas
- [ ] Script `exemplo_uso.py` testado
- [ ] Testes passando

Pronto! 🎉 Sua LLM está configurada e funcionando.
