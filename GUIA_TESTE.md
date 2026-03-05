# Guia de Teste e Uso do SerHu Orchestrator

## 📋 Pré-requisitos

1. **Python 3.11+** instalado
2. **Qdrant** (banco vetorial) - pode usar cloud ou local
3. **Supabase** (banco relacional) - pode usar cloud grátis

---

## 🚀 Configuração Inicial

### 1. Instalar dependências

```bash
cd packages/orchestrator
pip install -e ".[dev]"
```

### 2. Configurar variáveis de ambiente

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

### 3. Configurar tabelas no Supabase

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

## 📊 Estrutura dos Modelos de Personalidade

### HEXACO (24 facetas)
Cada fator tem 4 facetas. Acesse assim:
- `personality.hexaco.sincerity`
- `personality.hexaco.sociability`
- `personality.hexaco.creativity`
- etc.

### TCI-R Temperamento (16 subscales)
**Não existem atributos agregados!** Use as subscales diretamente:

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
- `personality.schwartz.stimulation`
- `personality.schwartz.achievement`
- `personality.schwartz.benevolence_caring`
- etc.

---

## 🌍 Suporte a Múltiplos Idiomas

O sistema agora suporta criação de Seres em **diferentes idiomas padrão**:
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

### Exemplo Multilíngue

Veja [exemplo_multilingue.py](exemplo_multilingue.py) para criar Seres em 4 idiomas:

```bash
python exemplo_multilingue.py
```

**Documentação completa**: [LANGUAGE_SUPPORT.md](LANGUAGE_SUPPORT.md)

---

## 🧪 Rodando os Testes

### Testes Unitários (SEM precisar de Qdrant/Supabase)

Os testes unitários usam mocks, então rodam rápido e offline:

```bash
# Da raiz do monorepo:
python -m pytest packages/orchestrator/tests/unit -v

# Ou de dentro do pacote:
cd packages/orchestrator
pytest tests/unit -v
```

### Testes de Integração (PRECISA das credenciais no .env)

Os testes de integração conectam nos serviços reais:

```bash
# Da raiz do monorepo:
python -m pytest packages/orchestrator/tests/integration -v -m integration

# Ou de dentro do pacote:
cd packages/orchestrator
pytest tests/integration -v -m integration
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
print(f"\nFatos semânticos: {len(context.facts)}")
print(f"Episódios arquivados: {len(context.archival)}")
```

### Exemplo 3: Atualizar Personalidade

```python
# Aplicar mudanças de traços baseado na interação
trait_updates = {
    "hexaco.sociability": 0.1,  # Aumenta sociabilidade
    "tci_temperament.exploratory_excitability": 0.05,  # Busca de novidade
    "tci_temperament.impulsiveness": 0.03,
    "schwartz.stimulation": 0.02,
}

context = orch.process_message(
    role="user",
    content="Vamos explorar lugares novos!",
    trait_deltas=trait_updates
)

# Ver nova personalidade
print(f"Sociabilidade atual: {orch.personality.hexaco.sociability}")
```

### Exemplo 4: Consolidar Memória (Twilight Phase)

```python
# Consolidar working memory → archival
summary = orch.consolidate()
print(f"Consolidação: {summary}")
```

### Exemplo 5: Ciclo de Sono (Dream Phase)

```python
# Executar ciclo de sono (NREM + REM)
sleep_result = orch.sleep()

print(f"Fatos extraídos: {len(sleep_result.facts_extracted)}")
print(f"Hipóteses geradas: {len(sleep_result.hypotheses)}")
print(f"Novas crenças: {len(sleep_result.beliefs_added)}")
```

### Exemplo 6: Carregar um Ser Existente

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
print(f"Estágio cognitivo: {orch.personality.development.stage}")
print(f"Interações: {orch.personality.development.interaction_count}")
```

### Exemplo 7: Obter System Prompt (para LLM)

```python
from serhu_orchestrator.personality.prompt_builder import build_system_prompt

# Gerar prompt de sistema baseado na personalidade atual
system_prompt = build_system_prompt(orch.personality)

print("=== SYSTEM PROMPT ===")
print(system_prompt)

# Agora você pode enviar esse prompt + contexto para um LLM (OpenAI, Claude, etc)
```

---

## 📝 Script de Exemplo Completo

Crie um arquivo `exemplo_uso.py` na raiz do monorepo:

```python
"""Exemplo de uso completo do Orchestrator."""

import os
from dotenv import load_dotenv
from serhu_orchestrator.orchestrator import Orchestrator
from serhu_orchestrator.personality.prompt_builder import build_system_prompt

load_dotenv()


def main():
    # 1. Criar ou carregar um Ser
    print("🌟 Criando um novo Ser...")
    
    orch = Orchestrator(
        qdrant_url=os.environ["QDRANT_URL"],
        qdrant_api_key=os.environ["QDRANT_API_KEY"],
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_key=os.environ["SUPABASE_KEY"],
        being_name="Estrela",
        working_memory_size=20,
    )
    
    being_id = orch.being_id
    print(f"✅ Ser criado! ID: {being_id}\n")

    # 2. Interagir
    print("💬 Conversando com o Ser...\n")
    
    messages = [
        ("user", "Olá! Me fale sobre você."),
        ("assistant", "Eu sou Estrela, um ser em desenvolvimento. Estou aprendendo sobre o mundo."),
        ("user", "O que te deixa curioso?"),
        ("assistant", "Estou curioso sobre as emoções humanas e como funcionam."),
    ]
    
    for role, content in messages:
        ctx = orch.process_message(role, content)
        print(f"[{role}] {content}")
    
    print(f"\n📊 Working memory size: {len(ctx.working)}")

    # 3. Ver personalidade
    print("\n🎭 Estado da Personalidade:")
    p = orch.personality
    print(f"  - Estágio cognitivo: {p.development.stage}")
    print(f"  - Interações: {p.development.interaction_count}")
    print(f"  - Sociabilidade (HEXACO): {p.hexaco.sociability:.2f}")
    print(f"  - Excitabilidade Exploratória (TCI): {p.tci_temperament.exploratory_excitability:.2f}")
    print(f"  - Empatia (Caráter TCI): {p.tci_character.empathy:.2f}")

    # 4. Consolidar memória
    print("\n🌙 Consolidando memória (twilight)...")
    summary = orch.consolidate()
    print(f"  {summary}")

    # 5. Ciclo de sono
    print("\n😴 Executando ciclo de sono...")
    sleep_result = orch.sleep()
    print(f"  Fatos extraídos: {len(sleep_result.facts_extracted)}")
    print(f"  Hipóteses geradas: {len(sleep_result.hypotheses)}")
    print(f"  Novas crenças: {len(sleep_result.beliefs_added)}")
    print(f"  Traits antes: {len(sleep_result.traits_before)} dims")
    print(f"  Traits depois: {len(sleep_result.traits_after)} dims")

    # 6. Gerar system prompt
    print("\n📜 System Prompt gerado:")
    print("=" * 60)
    prompt = build_system_prompt(p)
    print(prompt[:500] + "...")  # Primeiros 500 chars
    print("=" * 60)

    print(f"\n✨ Exemplo concluído! Being ID para reusar: {being_id}")


if __name__ == "__main__":
    main()
```

Execute:

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

Se os testes de integração forem pulados, é porque as variáveis de ambiente não estão configuradas ou os serviços não estão acessíveis.

---

## 📚 Próximos Passos

1. **Conectar com um LLM**: Use o `build_system_prompt()` + contexto para enviar para OpenAI/Anthropic
2. **Interface Web**: Crie um frontend que chame o Orchestrator
3. **Visualização 3D**: Use os dados de personalidade para gerar a forma visual do Ser
4. **Evolução Contínua**: Implemente lógica para atualizar traços baseado nas interações

---

## 🎯 Conceitos-Chave

- **Working Memory**: Memória de curto prazo (últimas N interações)
- **Archival Memory**: Memória de longo prazo vetorial (Qdrant)
- **Relational Memory**: Memória estruturada (Supabase) - personalidade, episódios, fatos
- **Consolidation**: Transferir working → archival
- **Sleep Cycle**: "Sonhar" para consolidar memórias e evoluir
- **Tabula Rasa**: O Ser começa "em branco" e aprende com o usuário

Bora testar! 🚀
