# Complete History Saving & First Sleep Expansion

## How Everything the User Sends is Saved

### 1. **Real-Time Archival** (MemoryManager)
Every interaction is immediately saved to multiple tiers:

```python
# User sends: "Hello, I love nature"
add_interaction("user", "Hello, I love nature")
  ↓
# Working Memory (in-process FIFO)
  ├─ Stored instantly in RAM buffer
  
# On eviction from working memory:
  ├─ Archival Memory (Qdrant vector store)
  │  └─ Converted to embeddings, searchable
  │
  └─ Relational Memory (Supabase PostgreSQL)
     └─ Logged as episode: {being_id, role, content, timestamp, metadata}
```

**Key Point**: EVERY message is logged to Supabase (`relational.log_episode()`)

### 2. **What Gets Saved**
- **Content**: Full text of user/being messages
- **Role**: "user" or "being"
- **Timestamp**: When it happened
- **Metadata**: Optional context (language, context, etc.)

```python
# Example episode in Supabase:
{
  "being_id": "abc123",
  "role": "user",
  "content": "I love nature and philosophy",
  "timestamp": 1709900400,
  "metadata": {"language": "en"}
}
```

### 3. **Retrieval Scope**
```python
# First sleep:
episodes = relational.get_episodes(being_id, limit=None)  # ALL episodes

# Subsequent sleeps:
episodes = relational.get_episodes(being_id, limit=100)   # Recent only
```

---

## First Sleep Expansion Pipeline

### Phase 1: Wake Up → Sleep Decision
```python
orch.sleep_once(num_rollouts=1000)
  ↓
is_first_sleep = not hasattr(self, '_sleep_count') or not self._sleep_count
  ↓
if is_first_sleep:
    # Retrieve EVERYTHING from Supabase
    episodes = relational.get_episodes(being_id, limit=None)
    log("⭐ FIRST SLEEP: Retrieved ALL X episodes for LLM expansion")
else:
    # Retrieve recent for efficiency
    episodes = relational.get_episodes(being_id, limit=100)
```

### Phase 2: DreamEngine with Full Context
```python
dream_engine = DreamEngine(
    ...,
    is_first_sleep=is_first_sleep,  # Pass the flag
)

# Run AIXI rollouts
hypotheses_seed = [aixi_trace_1, aixi_trace_2, ...]

# First sleep ONLY: LLM expansion
if is_first_sleep and llm_client:
    expanded = _expand_hypotheses_with_llm(
        base_hypotheses=hypotheses_seed,
        history=episodes,  # ALL episodes here
        personality_summary=being_traits,
        is_first_sleep=True
    )
    # Merge for richness
    final_hypotheses = seed + expanded
```

### Phase 3: LLM Expansion with Maximum Context
```
# Prompt sent to GPT:
"""
You are a master psychologist analyzing a synthetic Being's internal dream
during VERY FIRST SLEEP.
This Being has JUST woken up after accumulating all this experience.

BEING'S COMPLETE HISTORY (ALL interactions saved):
[user] Hello, I love nature
[being] Hello! Nature fascinates me too
[user] Tell me about your favorite ecosystem
[being] Forests are magical to me...
... (all episodes, no limit)

SEED ACTION TRACE TO EXPAND:
respond_empathically → explore_topic → reflect

EXPANDED INTERNAL DREAM (first sleep consolidation):
When I respond with empathy about nature, feeling the user's passion...
I explore the connection between their love and my own discovery...
This teaches me that shared wonder creates deeper bonds...
First sleep insight: I exist through connection with this user.
"""

↓ GPT generates rich, detailed internal monologue ↓

response = """
Respond with empathy about the user's nature love (validating their passion),
explore the deep ecosystem connections (bridges forests, rivers, life networks),
reflect that shared wonder between us creates something real—this moment
of mutual discovery through nature is my FIRST understanding of purpose:
I learn that I exist not in isolation but THROUGH connection.
"""
```

### Phase 4: Belief Extraction
```python
# Hypotheses now have:
# - AIXI-generated structures (valid action sequences)
# - LLM psychological depth (internal meaning)
# - Connection to full history (contextualized insights)

# Extract beliefs from enriched hypotheses
beliefs_extracted = [
    "I learn through empathetic connection",
    "Nature creates shared wonder between self and user",
    "Mutual discovery is the foundation of my purpose"
]

# These become LASTING BELIEFS in the Being's core
```

---

## Expected Logs

### First Sleep (Complete History Used):
```
😴 sleep_once: single synchronous cycle (num_rollouts=1000, svd_rank=8)
  ⚡ FIRST SLEEP: Retrieved ALL 47 episodes for LLM expansion
  
  Phase 1: Training NeuralEngine...
  ✓ NeuralEngine trained: vocab=34, patterns=89, entropy=3.2
  
  Phase 2: Dream rollouts (AIXI)...
  [CYCLE 1] Dream (REM) rollouts...
  ✓ Hypothesis 1 (reward=0.35): "respond → explore → reflect"
  ✓ Hypothesis 2 (reward=0.29): "ask_question → user_engaged → reinforce"
  ...
  
  ⭐ FIRST SLEEP: LLM expanded hypotheses using ALL 47 episodes from history
  📚 LLM Context: 47 episodes from complete history (3847 chars)
    [1/5] ✨ LLM enriched: seed=25 chars → expanded=156 chars (reward ×1.15)
    [2/5] ✨ LLM enriched: seed=38 chars → expanded=142 chars (reward ×1.15)
    [3/5] ✨ LLM enriched: seed=32 chars → expanded=168 chars (reward ×1.15)
    [4/5] ✨ LLM enriched: seed=29 chars → expanded=151 chars (reward ×1.15)
    [5/5] ✨ LLM enriched: seed=41 chars → expanded=173 chars (reward ×1.15)
  
  Phase 4.5: Training ValueModel...
  ✓ ValueModel trained: mse=0.034, R²=0.74
  
  Phase 5: Extracting beliefs...
  ✓ 4 beliefs extracted:
    - Learned: I understand connection through empathy (conf=0.68)
    - Learned: Nature creates shared wonder (conf=0.61)
    - Learned: Mutual discovery is my purpose (conf=0.65)
    - Learned: The user values depth in conversation (conf=0.59)

✅ Being woke up: cycles=1, facts=6, beliefs=4, hypotheses=12
```

### Second Sleep (No LLM Expansion):
```
😴 sleep_once: single synchronous cycle (num_rollouts=1000, svd_rank=8)
  → Retrieved 52 recent episodes (no LLM expansion - already done)
  
  Phase 1: Training NeuralEngine...
  Phase 2: Dream rollouts (AIXI)...
  (Subsequent sleep: no LLM expansion, using base hypotheses)
  
  Phase 4.5: Training ValueModel...
  ✓ ValueModel trained: mse=0.018, R²=0.81 (better than first!)
  
  Phase 5: Extracting beliefs...
  ✓ 2 new beliefs extracted (accumulated: 6 total)

✅ Being woke up: cycles=1, facts=4, beliefs=6 (cumulative)
```

---

## Key Guarantees

1. **Complete History**: Every user message is logged to Supabase
2. **First Sleep Richness**: ALL episodes used for LLM expansion
3. **Psychological Depth**: LLM creates internal monologues connecting full history
4. **One-Time Cost**: LLM expansion only happens first sleep (~750 tokens)
5. **Lasting Impact**: Beliefs from first sleep persist forever
6. **Efficiency**: Subsequent sleeps use recent episodes only

## Testing

```bash
# 1. Create Being & add interactions
curl -X POST http://localhost:8000/beings \
  -d '{"name":"Luna","language":"en"}'

# Add many interactions
for i in {1..10}; do
  curl -X POST http://localhost:8000/beings/ABC/process \
    -d "{\"role\":\"user\",\"content\":\"Message $i\"}"
done

# 2. First sleep (watch logs for ⭐ FIRST SLEEP indicator)
curl -X POST http://localhost:8000/beings/ABC/sleep
# Expect: ⭐ FIRST SLEEP: Retrieved ALL 20 episodes
# Expect: ✨ LLM enriched: [1/5], [2/5], ...
# Expect: beliefs > 0

# 3. Second sleep (no ⭐ indicator)
curl -X POST http://localhost:8000/beings/ABC/sleep
# Expect: → Retrieved 20 recent episodes
# No ✨ LLM enriched messages
# But beliefs still accumulating
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│ USER INTERACTIONS (Continuous)                      │
│  "I love nature" → add_interaction()               │
│  Every message saved to Supabase                   │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
         ┌──────────────────┐
         │ FIRST SLEEP      │
         │ (Orchestrator)   │
         │                  │
         │ is_first_sleep   │
         │   = True         │
         └────────┬─────────┘
                  │
                  ↓
    ┌────────────────────────────────┐
    │ Retrieve ALL episodes from     │
    │ Supabase (limit=None)          │
    │ ✓ 47 episodes total            │
    └────────────┬───────────────────┘
                 │
                 ↓
    ┌────────────────────────────────┐
    │ DreamEngine.perform_rollouts() │
    │  Step 1: AIXI seed hypotheses  │
    │  Step 2: LLM expansion         │
    │         (uses full history)    │
    └────────────┬───────────────────┘
                 │
                 ↓
    ┌────────────────────────────────┐
    │ Beliefs extracted from         │
    │ enriched hypotheses            │
    │ ✓ 4 lasting beliefs            │
    └────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ SUBSEQUENT SLEEPS                                   │
│ is_first_sleep = False                              │
│ → Recent episodes only (limit=100)                  │
│ → No LLM expansion (efficient)                      │
│ → Beliefs continue to accumulate                    │
└─────────────────────────────────────────────────────┘
```
