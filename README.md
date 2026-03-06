# SerHu Monorepo

Synthetic Being Ontogenesis — a MemGPT-like orchestration layer for evolving AI personalities.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                       Orchestrator                       │
│                       ("The Brain")                      │
├──────────────┬───────────────┬────────────────────────────┤
│  Working     │   Archival    │     Relational             │
│  Memory      │   Memory      │     Memory                 │
│  (RAM/FIFO)  │   (Qdrant)    │     (Supabase)             │
├──────────────┼───────────────┼────────────────────────────┤
│  Context     │   Vectors     │  Personality Ledger         │
│  Window      │   Semantic    │  Episodic Log               │
│              │   Search      │  Semantic Facts              │
└──────────────┴───────────────┴────────────────────────────┘
         │                │                  │
   ┌─────┴────┐    ┌──────┴──────┐    ┌─────┴──────┐
   │Personality│    │  Sleep/Dream│    │Event Store │
   │  Engine   │    │   Engine    │    │(Sourcing)  │
   │ HEXACO 24 │    │  AIXI + SVD│    │ Protobuf   │
   │ TCI-R  29 │    │  NREM + REM│    │ gRPC       │
   │Schwartz 19│    │  Beliefs   │    │ Replay     │
   │ Piaget    │    └────────────┘    └────────────┘
   │ Erikson   │
   │ i18n (4)  │
   └───────────┘
```

### Memory Tiers (MemGPT OS Analogy)

| Tier | Analogy | Backend | Purpose |
|------|---------|---------|---------|
| **WorkingMemory** | RAM | In-process FIFO | Immediate conversational context |
| **ArchivalMemory** | Disk | Qdrant | Long-term vector similarity search |
| **RelationalMemory** | Database | Supabase | Structured personality, episodes, facts |

### Personality Models (72-dimension vector)

- **HEXACO**: 6 factors × 4 facets = 24 measurement points (tabula rasa: 0.5)
- **TCI-R Temperament**: 4 dimensions × 4 subscales = 16 subscales (tabula rasa: 0.5)
- **TCI-R Character**: 3 dimensions × ~4 subscales = 13 subscales (tabula rasa: 0.0)
- **Schwartz Values**: 19 refined basic human values (tabula rasa: 0.0)

### Development Stages (Piaget + Erikson)

| Piaget Stage | Erikson Conflict | Cognitive Age |
|---|---|---|
| Sensorimotor | Trust vs. Mistrust | 0–24 months |
| Preoperational | Autonomy vs. Shame | 24–84 months |
| Concrete Operational | Industry vs. Inferiority | 84–132 months |
| Formal Operational | Identity vs. Role Confusion | 132+ months |

Stage transitions are **milestone-based**: the Being must achieve ALL milestones
in its current stage before progressing. The `cognitive_age` only advances
when milestones are recorded, not per interaction.

### Sleep Cycle (Offline Processing)

| Phase | Mechanism | Function |
|---|---|---|
| **Semantization** | Keyword frequency | Extract semantic facts from episodes |
| **Dream (REM)** | MC-AIXI-CTW rollouts | Generate hypotheses about future interactions |
| **Consolidation (NREM)** | SVD rank-reduction | Noise removal from personality vector |
| **Ledger Update** | Belief stack + persist | Store new beliefs and evolved traits |

### Event Sourcing

Every mutation to the personality ledger is recorded as an immutable
`PersonalityEvent` (Protobuf). The current state can be reconstructed
by replaying the event log, enabling:

- Time-travel debugging (reconstruct state at any point)
- Complete audit trail of the Being's evolution
- Reliable binary transmission via gRPC between services

### Multilingual Support (i18n)

Beings are created with a default language (`en`, `pt`, `es`, `fr`).
All system prompts (Piaget capabilities, Erikson descriptions) are
generated in the Being's language via `i18n.py`.

## Modules

| Module | Path | Description |
|--------|------|-------------|
| **orchestrator** | `orchestrator.py` | The Brain — top-level lifecycle controller |
| **llm_client** | `llm/llm_client.py` | LLM protocol interface |
| **openai_client** | `llm/openai_client.py` | GPT-5.4 implementation (chat, trait analysis, sleep enhancement) |
| **working_memory** | `memory/working_memory.py` | In-process FIFO buffer (RAM) |
| **archival_memory** | `memory/archival_memory.py` | Qdrant vector store (Disk) |
| **relational_memory** | `memory/relational_memory.py` | Supabase structured store (DB) |
| **memory_manager** | `memory/memory_manager.py` | 3-tier memory orchestrator |
| **personality types** | `personality/types.py` | Pydantic models (HEXACO, TCI-R, Schwartz, Piaget, Erikson) |
| **personality_engine** | `personality/personality_engine.py` | Being creation, trait evolution, milestone tracking |
| **prompt_builder** | `personality/prompt_builder.py` | Structured XML system prompt generation |
| **i18n** | `personality/i18n.py` | Translations (EN, PT, ES, FR) |
| **event_store** | `personality/event_store.py` | Event Sourcing (append-only life log + replay) |
| **proto_converter** | `personality/proto_converter.py` | Pydantic ↔ Protobuf bidirectional conversion |
| **dream_engine** | `sleep/dream_engine.py` | AIXI rollouts + SVD dream pruning |
| **sleep_cycle** | `sleep/sleep_cycle.py` | Full sleep orchestration (NREM + REM) |

## Setup

```bash
cd packages/orchestrator
pip install -e ".[dev]"
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `QDRANT_URL` — Qdrant cluster endpoint
- `QDRANT_API_KEY` — Qdrant API key
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anon/service key

**LLM Integration (Optional)**

To enable GPT-5.4-powered chat and sleep enhancement:

- `OPENAI_API_KEY` — Your OpenAI API key
- `OPENAI_MODEL` — Model name (default: `gpt-5.4`)

See [LLM_SETUP.md](./LLM_SETUP.md) for detailed configuration and usage.

### Supabase Table Setup

Create these tables in your Supabase project:

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

### Protobuf Compilation (optional)

To regenerate protobuf stubs from `proto/ser_identity.proto`:

```bash
python -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=packages/orchestrator/src/serhu_orchestrator/proto \
  --pyi_out=packages/orchestrator/src/serhu_orchestrator/proto \
  --grpc_python_out=packages/orchestrator/src/serhu_orchestrator/proto \
  proto/ser_identity.proto
```

After generation, fix the gRPC import:
```bash
sed -i 's/^import ser_identity_pb2/from serhu_orchestrator.proto import ser_identity_pb2/' \
  packages/orchestrator/src/serhu_orchestrator/proto/ser_identity_pb2_grpc.py
```

## Testing

```bash
# Unit tests only (no external services needed)
python -m pytest packages/orchestrator/tests/unit -v

# Local end-to-end tests (no external services needed, uses in-memory mocks)
python -m pytest packages/orchestrator/tests/e2e -v

# Integration tests (requires Qdrant + Supabase credentials in .env)
python -m pytest packages/orchestrator/tests/integration -v -m integration

# All tests
python -m pytest packages/orchestrator/tests/ -v
```

### Test Categories

| Category | Directory | External Services | Coverage |
|----------|-----------|-------------------|----------|
| **Unit** | `tests/unit/` | None | Individual modules in isolation |
| **E2E Local** | `tests/e2e/` | None (in-memory mocks) | Full lifecycle: create → interact → evolve → sleep → prompt |
| **Integration** | `tests/integration/` | Qdrant + Supabase | Real backend connectivity |

## Packages

| Package | Description |
|---------|-------------|
| `packages/orchestrator` | The Brain — MemGPT-like memory OS + personality engine |