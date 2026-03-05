# Guia de Teste e Uso do SerHu Orchestrator

## 📋 Pré-requisitos

1. **Python 3.11+** instalado
2. **Qdrant** (banco vetorial) - pode usar cloud ou local *(necessário apenas para testes de integração)*
3. **Supabase** (banco relacional) - pode usar cloud grátis *(necessário apenas para testes de integração)*

---

## 🚀 Configuração Inicial

### 1. Instalar dependências

```bash
cd packages/orchestrator
pip install -e ".[dev]"
```

### 2. Configurar variáveis de ambiente (apenas para integração)

Crie um arquivo `.env` na raiz do monorepo:

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
# Qdrant vector database
QDRANT_URL=https://seu-cluster.cloud.qdrant.io
QDRANT_API_KEY=sua-chave-qdrant

# Supabase relational database
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-supabase
```

### 3. Configurar tabelas no Supabase (apenas para integração)

Acesse o SQL Editor no seu projeto Supabase e execute:

```sql
CREATE TABLE personality_ledger (
    being_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    updated_at FLOAT NOT NULL
);

CREATE TABLE episodic_log (
    id BIGSERIAL PRIMARY KEY,
    being_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at FLOAT NOT NULL
);

CREATE TABLE semantic_facts (
    id BIGSERIAL PRIMARY KEY,
    being_id TEXT NOT NULL,
    fact TEXT NOT NULL,
    source_episodes TEXT DEFAULT '[]',
    created_at FLOAT NOT NULL
);
```

---

## 📊 Estrutura dos Modelos de Personalidade (72 dimensões)

### HEXACO (24 facetas)
Cada fator tem 4 facetas. Tabula rasa: 0.5 (ponto neutro).
- `personality.hexaco.sincerity`
- `personality.hexaco.sociability`
- `personality.hexaco.creativity`
- etc.

### TCI-R Temperamento (16 subscales)
**Não existem atributos agregados!** Use as subscales diretamente.
Tabula rasa: 0.5 (ponto neutro).

**Novelty Seeking (NS):**
- `personality.tci_temperament.exploratory_excitability`
- `personality.tci_temperament.impulsiveness`
- `personality.tci_temperament.extravagance`
- `personality.tci_temperament.disorderliness`

**Harm Avoidance (HA):**
- `personality.tci_temperament.anticipatory_worry`
- `personality.tci_temperament.fear_of_uncertainty`
- `personality.tci_temperament.shyness`
- `personality.tci_temperament.fatigability`

**Reward Dependence (RD):**
- `personality.tci_temperament.sentimentality_rd`
- `personality.tci_temperament.openness_to_communication`
- `personality.tci_temperament.attachment`
- `personality.tci_temperament.dependence_rd`

**Persistence (PS):**
- `personality.tci_temperament.eagerness_of_effort`
- `personality.tci_temperament.work_hardened`
- `personality.tci_temperament.ambitious`
- `personality.tci_temperament.perfectionist_ps`

### TCI-R Character (13 subscales)
Caráter é **aprendido**, começa em 0.0:

**Self-Directedness:**
- `personality.tci_character.responsibility`
- `personality.tci_character.purposefulness`
- `personality.tci_character.resourcefulness`
- `personality.tci_character.self_acceptance`
- `personality.tci_character.enlightened_second_nature`

**Cooperativeness:**
- `personality.tci_character.social_acceptance`
- `personality.tci_character.empathy`
- `personality.tci_character.helpfulness`
- `personality.tci_character.compassion`

**Self-Transcendence:**
- `personality.tci_character.self_forgetfulness`
- `personality.tci_character.transpersonal_identification`
- `personality.tci_character.spiritual_acceptance`
- `personality.tci_character.pure_conscience`

### Schwartz Values (19 valores)
Tabula rasa: 0.0 (não formados). Valores representam o que o Ser *aspira*, não o que ele *é*.
- `personality.schwartz.stimulation`
- `personality.schwartz.achievement`
- `personality.schwartz.benevolence_caring`
- etc.

---

## 🌍 Suporte a Múltiplos Idiomas

O sistema suporta criação de Seres em **diferentes idiomas padrão**:
- 🇬🇧 English (`en`) - Padrão
- 🇧🇷 Português (`pt`)
- 🇪🇸 Español (`es`)
- 🇫🇷 Français (`fr`)

O idioma configura:
- **System prompts** (Piaget, Erikson)
- **Descrições cognitivas** (capacidades e limitações)
- **Interface do Ser** (tudo em seu idioma preferido)

### Exemplo: Criar um Ser em Português

```python
orch = Orchestrator(
    qdrant_url="...",
    qdrant_api_key="...",
    supabase_url="...",
    supabase_key="...",
    being_name="Lua",
    language="pt",  # ← Define idioma português
)

prompt = build_system_prompt(orch.personality)
# Prompt incluirá: "Você está navegando CONFIANÇA vs. DESCONFIANÇA..."
```

**Documentação completa**: [LANGUAGE_SUPPORT.md](LANGUAGE_SUPPORT.md)

---

## 🧪 Rodando os Testes

### Testes Unitários (SEM precisar de Qdrant/Supabase)

Os testes unitários usam mocks, então rodam rápido e offline:

```bash
# Da raiz do monorepo:
python -m pytest packages/orchestrator/tests/unit -v
```

### Testes Ponta a Ponta Local (SEM precisar de Qdrant/Supabase)

Os testes E2E locais exercitam o **ciclo de vida completo** do Orchestrator
usando backends in-memory (sem Qdrant/Supabase reais):

```bash
# Da raiz do monorepo:
python -m pytest packages/orchestrator/tests/e2e -v
```

O que é testado no E2E local:
- ✅ Criação de Ser (tabula rasa)
- ✅ Interações com evolução de traços
- ✅ Overflow de memória de trabalho → archival
- ✅ Consolidação (twilight)
- ✅ Ciclo de sono (AIXI + SVD)
- ✅ Progressão de milestones (Piaget completo)
- ✅ Event Sourcing (replay de eventos)
- ✅ Round-trip Protobuf (serialização/deserialização)
- ✅ Geração de prompts em 4 idiomas (EN, PT, ES, FR)

### Testes de Integração (PRECISA das credenciais no .env)

Os testes de integração conectam nos serviços reais:

```bash
# Da raiz do monorepo:
python -m pytest packages/orchestrator/tests/integration -v -m integration
```

### Todos os testes

```bash
python -m pytest packages/orchestrator/tests/ -v
```

---

## 💻 Usando o Orchestrator no Código

### Exemplo 1: Criar um Ser (Being) do Zero

```python
from serhu_orchestrator.orchestrator import Orchestrator

# Criar um novo Ser (tabula rasa)
orch = Orchestrator(
    qdrant_url="https://seu-cluster.cloud.qdrant.io",
    qdrant_api_key="sua-chave",
    supabase_url="https://seu-projeto.supabase.co",
    supabase_key="sua-chave",
    being_name="Lua",  # Nome do seu ser
    language="pt",     # Idioma padrão
    working_memory_size=50,  # Tamanho da "RAM"
)

print(f"Ser criado! ID: {orch.being_id}")
print(f"Personalidade inicial: {orch.personality}")
```

### Exemplo 2: Conversar com o Ser

```python
# Processar uma mensagem do usuário
context = orch.process_message(
    role="user",
    content="Olá! Como você está?"
)

# Ver o contexto atual (working memory)
print("Memória de trabalho:")
for entry in context.working:
    print(f"  [{entry.role}] {entry.content}")

# Ver fatos e episódios recuperados
print(f"\nFatos semânticos: {len(context.semantic_facts)}")
print(f"Resultados archival: {len(context.archival_results)}")
```

### Exemplo 3: Atualizar Personalidade

```python
# Aplicar mudanças de traços baseado na interação
# FORMATO: dict aninhado {modelo: {faceta: delta}}
context = orch.process_message(
    role="user",
    content="Vamos explorar lugares novos!",
    trait_deltas={
        "hexaco": {"sociability": 0.1, "inquisitiveness": 0.05},
        "tci_temperament": {"exploratory_excitability": 0.05},
        "schwartz": {"stimulation": 0.02},
    },
)

# Ver nova personalidade
print(f"Sociabilidade atual: {orch.personality.hexaco.sociability}")
```

### Exemplo 4: Registrar Milestone (Piaget)

```python
# Registrar que o Ser alcançou um marco cognitivo
engine = orch._personality_engine
state = engine.record_milestone(orch.personality, "object_permanence")

print(f"Estágio: {state.development.stage}")
print(f"Idade cognitiva: {state.development.cognitive_age}")
print(f"Milestones: {state.development.milestones_achieved}")
```

### Exemplo 5: Consolidar Memória (Twilight Phase)

```python
# Consolidar working memory → archival
archived = orch.consolidate()
print(f"Entradas arquivadas: {archived}")
```

### Exemplo 6: Ciclo de Sono (Dream Phase)

```python
# Executar ciclo de sono (NREM + REM)
sleep_result = orch.sleep(num_rollouts=1000, svd_rank=8, seed=42)

print(f"Fatos extraídos: {len(sleep_result.facts_extracted)}")
print(f"Hipóteses geradas: {len(sleep_result.hypotheses)}")
print(f"Novas crenças: {len(sleep_result.beliefs_added)}")
print(f"Traits antes: {len(sleep_result.traits_before)} dims")
print(f"Traits depois: {len(sleep_result.traits_after)} dims")
```

### Exemplo 7: Event Sourcing

```python
from serhu_orchestrator.personality.event_store import EventStore

# Criar event store para um Ser
store = EventStore(ser_id=orch.being_id)

# Registrar eventos
store.record_being_created(name="Lua", language="pt")
store.record_trait_update({"hexaco": {"sincerity": 0.1}})
store.record_milestone("object_permanence", new_cognitive_age=6.0)
store.record_belief("core", "O mundo é seguro.")

# Reconstruir estado a partir dos eventos
state = store.replay()
print(f"Nome: {state.name}")
print(f"Sinceridade: {state.hexaco.sincerity}")
print(f"Idade cognitiva: {state.development.cognitive_age}")

# Replay parcial (até evento 2)
partial = store.replay(up_to_sequence=2)
```

### Exemplo 8: Serialização Protobuf

```python
from serhu_orchestrator.personality.proto_converter import (
    personality_to_ledger,
    ledger_to_personality,
)

# Converter para Protobuf (binário compacto)
ledger = personality_to_ledger(orch.personality)
binary = ledger.SerializeToString()
print(f"Tamanho binário: {len(binary)} bytes")

# Converter de volta para Pydantic
restored = ledger_to_personality(ledger)
assert restored.being_id == orch.personality.being_id
```

### Exemplo 9: Carregar um Ser Existente

```python
# Se você já tem um Being criado
existing_being_id = "abc123-def456-..."

orch = Orchestrator(
    qdrant_url="...",
    qdrant_api_key="...",
    supabase_url="...",
    supabase_key="...",
    being_id=existing_being_id,  # Carrega existente
)

print(f"Ser {orch.personality.name} carregado!")
print(f"Idioma: {orch.personality.language}")
print(f"Estágio cognitivo: {orch.personality.development.stage}")
print(f"Conflito Erikson: {orch.personality.development.erikson_conflict}")
print(f"Interações: {orch.personality.development.interaction_count}")
```

### Exemplo 10: Obter System Prompt (para LLM)

```python
# Gerar prompt de sistema baseado na personalidade atual
prompt = orch.build_prompt()

print("=== SYSTEM PROMPT ===")
print(prompt)

# O prompt inclui:
# - Tag de identidade (nome, idioma, estágio)
# - Conflito Erikson no idioma do Ser
# - 72 scores de personalidade (HEXACO, TCI-R, Schwartz)
# - Restrições cognitivas (Piaget)
# - Crenças (core + surface)
```

---

## 📝 Script de Exemplo Completo

Execute o exemplo incluído na raiz do monorepo:

```bash
python exemplo_uso.py
```

---

## 🔍 Troubleshooting

### Erro: "QDRANT_URL not set"

Verifique se o arquivo `.env` existe e tem as variáveis corretas.

```bash
cat .env
```

### Erro: "Cannot resolve Qdrant host"

Verifique sua conexão de internet ou se a URL do Qdrant está correta.

### Erro ao instalar dependências

Certifique-se de estar no diretório correto:

```bash
cd packages/orchestrator
pip install -e ".[dev]"
```

### Testes pulando (SKIPPED)

Se os testes de integração forem pulados, é porque as variáveis de ambiente não estão configuradas ou os serviços não estão acessíveis. Use os **testes E2E locais** como alternativa:

```bash
python -m pytest packages/orchestrator/tests/e2e -v
```

---

## 🎯 Conceitos-Chave

- **Working Memory**: Memória de curto prazo (últimas N interações)
- **Archival Memory**: Memória de longo prazo vetorial (Qdrant)
- **Relational Memory**: Memória estruturada (Supabase) - personalidade, episódios, fatos
- **Consolidation**: Transferir working → archival
- **Sleep Cycle**: "Sonhar" para consolidar memórias e evoluir (AIXI + SVD)
- **Tabula Rasa**: O Ser começa "em branco" e aprende com o usuário
- **Milestones**: Marcos cognitivos que avançam a idade (Piaget)
- **Erikson Conflicts**: Desafios psicossociais mapeados ao estágio atual
- **Event Sourcing**: Log imutável de todos os eventos da vida do Ser
- **Protobuf**: Serialização binária para comunicação entre serviços (gRPC)
- **i18n**: Suporte multilíngue (EN, PT, ES, FR)

Bora testar! 🚀
