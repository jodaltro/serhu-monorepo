# SerHu Monorepo

Synthetic Being Ontogenesis — a MemGPT-like orchestration layer for evolving AI personalities.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  Orchestrator                     │
│                  ("The Brain")                    │
├─────────────┬──────────────┬─────────────────────┤
│  Working    │   Archival   │    Relational        │
│  Memory     │   Memory     │    Memory            │
│  (RAM/FIFO) │   (Qdrant)   │    (Supabase)        │
├─────────────┼──────────────┼─────────────────────┤
│  Context    │   Vectors    │  Personality Ledger   │
│  Window     │   Semantic   │  Episodic Log         │
│             │   Search     │  Semantic Facts       │
└─────────────┴──────────────┴─────────────────────┘
                      │
          ┌───────────┴───────────┐
          │  Personality Engine   │
          │  HEXACO (24 facets)   │
          │  TCI-R  (29 scales)   │
          │  Schwartz (19 values) │
          │  Piaget stages        │
          └───────────────────────┘
```

### Memory Tiers (MemGPT OS Analogy)

| Tier | Analogy | Backend | Purpose |
|------|---------|---------|---------|
| **WorkingMemory** | RAM | In-process FIFO | Immediate conversational context |
| **ArchivalMemory** | Disk | Qdrant | Long-term vector similarity search |
| **RelationalMemory** | Database | Supabase | Structured personality, episodes, facts |

### Personality Models

- **HEXACO**: 6 factors × 4 facets = 24 measurement points (tabula rasa: 0.5)
- **TCI-R Temperament**: 4 dimensions × 4 subscales = 16 subscales (tabula rasa: 0.5)
- **TCI-R Character**: 3 dimensions × ~4 subscales = 13 subscales (tabula rasa: 0.0)
- **Schwartz Values**: 19 refined basic human values (tabula rasa: 0.0)

### Development Stages (Piaget)

Sensorimotor → Preoperational → Concrete Operational → Formal Operational

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

## Testing

```bash
# Unit tests only (no external services needed)
python -m pytest packages/orchestrator/tests/unit -v

# Integration tests (requires Qdrant + Supabase credentials in .env)
python -m pytest packages/orchestrator/tests/integration -v -m integration

# All tests
python -m pytest packages/orchestrator/tests/ -v
```

## Packages

| Package | Description |
|---------|-------------|
| `packages/orchestrator` | The Brain — MemGPT-like memory OS + personality engine |