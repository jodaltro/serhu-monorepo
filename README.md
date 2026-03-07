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
   │ HEXACO 24 │    │ Solomonoff  │    │ Protobuf   │
   │ TCI-R  29 │    │  AIXI + SVD│    │ gRPC       │
   │Schwartz 19│    │ NeuralEngine│    │ Replay     │
   │ Piaget    │    │ Self-Learn  │    └────────────┘
   │ Erikson   │    └────────────┘
   │ i18n (4)  │
   │ Ledger    │
   │ Interpret │
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

### Progressive Language Evolution (Stage-Aware Prompting)

The Being does NOT start speaking fluently. Language evolves gradually:

| Stage | Language Level | Prompt Strategy | Max Tokens |
|---|---|---|---|
| Sensorimotor (0-6m) | Pre-verbal: sounds only | `<output_rules>` + no personality | 15 |
| Sensorimotor (6-12m) | Babbling, proto-words | `<output_rules>` + no personality | 25 |
| Sensorimotor (12-24m) | 1-2 word fragments | `<output_rules>` + no personality | 40 |
| Preoperational (2-7y) | Simple sentences, "why?" | Temperament only + limited ledger | 150 |
| Concrete Operational (7-11y) | Logical, organized | Full personality + ledger | 512 |
| Formal Operational (11+y) | Sophisticated, abstract | Full personality + ledger | 1024 |

The prompt builder generates **different prompt structures per stage** via
`_build_sensorimotor_prompt()`, `_build_preoperational_prompt()`, and
`_build_full_prompt()`. Token limits are enforced via `_stage_llm_params()`.

### Sleep Cycle (Offline Processing — Self-Learning)

The sleep cycle is the Being's primary mechanism for building its own
internal language model.  The LLM (if available) is used **only once
at the start** of sleep to extract the AIXI environment inputs.  All
subsequent rollouts run autonomously.

| Phase | Mechanism | Function |
|---|---|---|
| **Environment Build** | LLM one-shot extraction (fallback: NeuralEngine patterns) | Build AIXI environment (actions, observations, rewards, transitions, horizon, gamma) |
| **Training** | NeuralEngine (TF-IDF + self-attention + n-gram mining) | Build internal model from episodic memories (transformer-inspired) |
| **Semantization** | NeuralEngine pattern analysis (fallback: keyword frequency) | Transform episodic memory → semantic memory (patterns, beliefs, facts) |
| **Dream (REM)** | MC-AIXI rollouts against `AixiEnvironment` (reset/step interface) | Generate hypotheses via environment simulation with discounted rewards |
| **Consolidation (NREM)** | SVD rank-reduction | Noise removal from personality vector |
| **Ledger Update** | NeuralEngine belief derivation + belief stack + persist | Derive beliefs from dreams, store evolved traits |
| **ValueModel Train** | Linear reward predictor on (state, action) → reward pairs | Pre-screen candidates online, cut rollout cost |
| **WorldModel Persist** | Store EnvironmentSpec + WorldModel + ValueModel in Orchestrator | Enable online planning during subsequent chat turns |

### Online Planning (Phase -1 — Real-Time Action Selection)

After at least one sleep cycle, the Being uses the consolidated WorldModel
during `chat()` to evaluate candidate responses via short AIXI rollouts:

| Step | Mechanism | Description |
|---|---|---|
| **Generate** | NeuralEngine × K variants | Produce K diverse response candidates |
| **Map** | Token overlap matching | Associate each candidate with closest AIXI action |
| **Pre-screen** | ValueModel.rank() (if trained) | Fast reward prediction to select top-3 for rollouts |
| **Evaluate** | AixiEnvironment mini-rollouts | Score top-3 candidates via Monte-Carlo simulation |
| **Select** | argmax(expected_reward) | Choose the candidate with highest expected reward |
| **Record** | Experience logging | Store real reward post-turn for calibration |

If no WorldModel is available (pre-sleep), the planner is skipped and `chat()`
falls back to direct NeuralEngine response generation.

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
| **neural_engine** | `sleep/neural_engine.py` | Transformer-inspired self-learning engine (TF-IDF, self-attention, n-gram patterns, response generation) |
| **llm_client** | `llm/llm_client.py` | LLM protocol interface (used for one-shot AIXI environment extraction at sleep start) |
| **openai_client** | `llm/openai_client.py` | OpenAI implementation (extract_environment_spec for AIXI) |
| **working_memory** | `memory/working_memory.py` | In-process FIFO buffer (RAM) |
| **archival_memory** | `memory/archival_memory.py` | Qdrant vector store (Disk) |
| **relational_memory** | `memory/relational_memory.py` | Supabase structured store (DB) |
| **memory_manager** | `memory/memory_manager.py` | 3-tier memory orchestrator |
| **personality types** | `personality/types.py` | Pydantic models (HEXACO, TCI-R, Schwartz, Piaget, Erikson) |
| **personality_engine** | `personality/personality_engine.py` | Being creation, trait evolution, milestone tracking |
| **prompt_builder** | `personality/prompt_builder.py` | Stage-aware system prompt generation: sensorimotor (output_rules), preoperational (temperament only), full (XML + ledger interpretation) |
| **i18n** | `personality/i18n.py` | Translations (EN, PT, ES, FR) |
| **event_store** | `personality/event_store.py` | Event Sourcing (append-only life log + replay) |
| **proto_converter** | `personality/proto_converter.py` | Pydantic ↔ Protobuf bidirectional conversion |
| **dream_engine** | `sleep/dream_engine.py` | AIXI rollouts against `AixiEnvironment` (reset/step) + SVD dream pruning |
| **sleep_cycle** | `sleep/sleep_cycle.py` | Full sleep orchestration (environment build → training → semantize → REM → NREM → value model → ledger) |
| **aixi_environment** | `sleep/aixi_environment.py` | RL-like AIXI environment (EnvironmentSpec, WorldModel, AixiEnvironment, EnvironmentBuilder) |
| **online_planner** | `sleep/online_planner.py` | Real-time AIXI mini-rollouts for action selection during chat (Phase -1) with ValueModel pre-screening |
| **value_model** | `sleep/value_model.py` | Lightweight linear reward predictor V(state, action) → reward for candidate pre-screening |

## Setup

```bash
# Install all packages in development mode
pip install -e "packages/orchestrator[dev]"
pip install -e "packages/morphogenesis[dev]"
pip install -e "packages/api[dev]"
pip install -e "packages/grpc_server[dev]"
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

**Note:** External LLM (GPT-5.4) is optional. When provided via `llm_client`,
it is used **only once at sleep start** to extract the AIXI environment
specification.  Without it, the NeuralEngine builds the environment from
its own learned patterns.

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

# Morphogenesis tests
python -m pytest packages/morphogenesis/tests/unit -v

# API tests (uses in-memory mocks)
python -m pytest packages/api/tests/unit -v

# gRPC server tests (direct + in-process channel)
python -m pytest packages/grpc_server/tests/unit -v

# Integration tests (requires Qdrant + Supabase credentials in .env)
python -m pytest packages/orchestrator/tests/integration -v -m integration

# ALL tests (395 Python + 9 JS, no external services)
python -m pytest packages/orchestrator/tests/unit packages/orchestrator/tests/e2e \
  packages/morphogenesis/tests/unit packages/api/tests/unit \
  packages/grpc_server/tests/unit -v
cd packages/frontend && npm test
```

### Test Categories

| Category | Directory | External Services | Tests | Coverage |
|----------|-----------|-------------------|-------|----------|
| **Orchestrator Unit** | `packages/orchestrator/tests/unit/` | None | 240 | Individual modules in isolation |
| **Orchestrator E2E** | `packages/orchestrator/tests/e2e/` | None (in-memory mocks) | 30 | Full lifecycle: create → interact → evolve → sleep → prompt |
| **Morphogenesis Unit** | `packages/morphogenesis/tests/unit/` | None | 26 | Color, geometry, animation engines |
| **API Unit** | `packages/api/tests/unit/` | None (in-memory mocks) | 16 | REST endpoints, CRUD, visual state |
| **gRPC Unit** | `packages/grpc_server/tests/unit/` | None | 16 | Servicer + in-process channel |
| **Frontend Unit** | `packages/frontend/tests/unit/` | None | 7 | API client (createBeing, chat, visual) |
| **Integration** | `packages/orchestrator/tests/integration/` | Qdrant + Supabase | — | Real backend connectivity |

## Packages

| Package | Description |
|---------|-------------|
| `packages/orchestrator` | The Brain — MemGPT-like memory OS + personality engine |
| `packages/api` | FastAPI REST API — exposes the Orchestrator to mobile/web clients |
| `packages/morphogenesis` | Visual Morphogenesis Engine — personality → color/shape/animation |
| `packages/grpc_server` | gRPC BeingService — Lambda ↔ Fargate binary communication |
| `packages/frontend` | Three.js web frontend — renders the Being in 3D cosmos with text chat |

## Application Modules

### API Server (`packages/api`)

REST API built with FastAPI, exposing the Orchestrator's full lifecycle:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/beings` | POST | Create a new Being (tabula rasa) |
| `/beings/{id}` | GET | Get Being summary |
| `/beings/{id}/personality` | GET | Full personality ledger (72-dim vector) |
| `/beings/{id}/chat` | POST | Chat with the Being (self-generated responses from learned patterns) |
| `/beings/{id}/process` | POST | Process message (manual mode, explicit trait deltas) |
| `/beings/{id}/consolidate` | POST | Consolidate working memory to archival |
| `/beings/{id}/sleep` | POST | Trigger full sleep cycle (NREM + REM) |
| `/beings/{id}/recall` | POST | Recall memories via semantic search |
| `/beings/{id}/learn` | POST | Store a semantic fact |
| `/beings/{id}/visual` | GET | Get visual morphogenesis state for renderer |

```bash
# Run the API server
cd packages/api && pip install -e ".[dev]"
uvicorn serhu_api.app:app --host 0.0.0.0 --port 8000
```

### Morphogenesis Engine (`packages/morphogenesis`)

Translates the 72-dimension personality vector into visual parameters
for 3D rendering (Three.js, Unity, Unreal, etc.):

| Component | Driven By | Output |
|-----------|-----------|--------|
| **Color** (HSL) | HEXACO + TCI dimensions | Hue (personality), Saturation (arousal), Lightness (valence) |
| **Geometry** | Agreeableness, Openness, Conscientiousness | Roundness, spikiness, symmetry, complexity, scale |
| **Animation** | TCI Temperament (NS, HA, RD, PS) | Pulse rate, movement speed, center attraction, glow, roughness |

Follows the Kiki/Bouba principle:
- Agreeable/cooperative → rounded, soft, spherical (Bouba)
- Assertive/novelty-seeking → angular, spiky, sharp (Kiki)

### gRPC Server (`packages/grpc_server`)

Implements the `BeingService` defined in `proto/ser_identity.proto`
for high-performance binary communication between services:

| RPC | Description |
|-----|-------------|
| `GetLedger` | Retrieve current personality ledger |
| `RecordEvent` | Record a new event in the life log |
| `ReplayEvents` | Reconstruct ledger at a point in time |
| `StreamEvents` | Server-side streaming for real-time sync |

```bash
# Run the gRPC server
cd packages/grpc_server && pip install -e ".[dev]"
python -m serhu_grpc.server --port 50051
```

### Frontend (`packages/frontend`)

Three.js web application that renders the Being as a 3D entity in a cosmic
starfield. The user interacts via text chat; the Being responds both verbally
and physically — its shape, color, and movement evolve in real-time as its
personality develops.

**Stack:** Vite + Three.js (vanilla ES modules)

**Morphogenesis 3D Pipeline:**
- `IcosahedronGeometry` (detail=4) base mesh with vertex displacement
- Kiki/Bouba deformation: `roundness` → spherical, `spikiness` → angular
- `MeshPhysicalMaterial` with emissive glow, clearcoat, PBR roughness
- Pulse breathing, Lissajous drift, rotation driven by temperament
- HSL color from personality (hue=trait, saturation=arousal, lightness=valence)

```bash
# Run the frontend dev server (proxies API calls to :8000)
cd packages/frontend && npm install
npm run dev      # → http://localhost:3000

# Build for production
npm run build

# Run tests
npm test
```