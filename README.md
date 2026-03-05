# SerHu Monorepo

Cognitive architecture for evolving artificial beings based on tabula rasa learning.

## Architecture

This monorepo implements the **Orchestration Layer** ("The Brain") — a MemGPT-inspired memory management system that organizes a Ser's knowledge across three tiers:

| Tier | Analogy | Backend | Purpose |
|------|---------|---------|---------|
| **Working Memory** | RAM | In-process buffer | Immediate conversation context (FIFO) |
| **Archival Memory** | Disk (semantic) | Qdrant | Long-term vector search for semantic recall |
| **Relational Memory** | Disk (structured) | Supabase | Persistent records, personality state, entity graphs |

### Personality Models

The Ser's personality is defined by high-granularity psychometric models:

- **HEXACO** — 6 domains × 4 facets = 24 trait dimensions
- **TCI-R** — 4 temperament + 3 character dimensions with subscales
- **Schwartz Values** — 19 refined basic human values

### Cognitive Development

The Ser progresses through Piaget's stages based on interaction count:

| Stage | Interactions | Capability |
|-------|-------------|------------|
| Sensorimotor | 0–49 | Pattern repetition, immediate reactions |
| Preoperational | 50–199 | Symbolic language, simple metaphors |
| Concrete Operational | 200–499 | Logical hierarchies, classification |
| Formal Operational | 500+ | Abstract reasoning, metacognition |

## Packages

| Package | Description |
|---------|-------------|
| `@serhu/orchestrator` | Core memory management and personality system |

## Setup

```bash
# Install dependencies
pnpm install

# Type check
pnpm lint

# Run unit tests
pnpm test:unit

# Run integration tests (requires .env with credentials)
pnpm test:integration

# Run all tests
pnpm test
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `QDRANT_URL` | Qdrant Cloud endpoint URL |
| `QDRANT_API_KEY` | Qdrant API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/publishable key |

### Supabase Schema

Create the following tables in your Supabase project:

```sql
-- Memory records table
CREATE TABLE memories (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ser_id TEXT NOT NULL,
  memory_type TEXT NOT NULL CHECK (memory_type IN ('episodic', 'semantic', 'causal', 'entity')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_memories_ser_id ON memories(ser_id);
CREATE INDEX idx_memories_type ON memories(memory_type);

-- Personality state snapshots
CREATE TABLE personality_states (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ser_id TEXT UNIQUE NOT NULL,
  state JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);
```