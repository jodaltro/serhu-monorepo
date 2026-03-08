# Testing First Sleep Expansion with Complete History

## Overview
This guide walks you through manually testing the implementation to verify:
1. **Complete history is saved** - Every user message goes to Supabase
2. **First sleep detects correctly** - ⚡ indicator shows in logs
3. **LLM expansion happens** - ⭐ indicator + character counts shown
4. **Beliefs are extracted** - beliefs > 0 (was always 0 before)
5. **ValueModel learns** - mse > 0, R² > 0 (was 0.0, 0.0 before)

---

## Prerequisites

1. **Environment Setup**
```bash
cd /home/jodaltro/jod_projetos/serhu-monorepo

# Install all packages
pip install -e packages/orchestrator
pip install -e packages/api
pip install -e packages/morphogenesis
pip install -e packages/grpc_server

# Verify environment variables
echo "OPENAI_API_KEY=${OPENAI_API_KEY:0:5}...***"  # Should NOT be empty
echo "SUPABASE_URL=${SUPABASE_URL:0:30}..."
echo "SUPABASE_KEY=${SUPABASE_KEY:0:5}...***"
echo "QDRANT_URL=${QDRANT_URL}"
```

2. **Verify Database Connectivity**
```bash
# Test Supabase
python -c "
from serhu_orchestrator.memory.relational_memory import RelationalMemory
rm = RelationalMemory('${SUPABASE_URL}', '${SUPABASE_KEY}')
print('✓ Supabase connected')
print(f'  Tables available: {rm._supabase.table(\"sleep_episodes\").select(\"*\").limit(1).execute()}')
"

# Test Qdrant
python -c "
from serhu_orchestrator.memory.archival_memory import ArchivalMemory
am = ArchivalMemory('${QDRANT_URL}')
print('✓ Qdrant connected')
print(f'  Collections: {am._client.get_collections()}')
"
```

---

## Test Scenario 1: Manual Orchestrator Test

### Step 1: Create a Being and Add History
```python
# test_first_sleep.py
from serhu_orchestrator.orchestrator import Orchestrator
import logging

logging.basicConfig(level=logging.INFO)

# Create Being
print("=" * 60)
print("STEP 1: Creating Being with Portuguese language")
print("=" * 60)
orch = Orchestrator(
    being_name="TestBeing",
    language="pt",
    qdrant_url="${QDRANT_URL}",
    qdrant_api_key="${QDRANT_API_KEY}",
    supabase_url="${SUPABASE_URL}",
    supabase_key="${SUPABASE_KEY}",
    llm_client=True,  # Enable LLM for expansion
)

being_id = orch._personality.being_id
print(f"\n✓ Created Being: {being_id}")
print(f"  Language: {orch._personality.language}")
print(f"  Stage: {orch._personality.piagetian_stage}")

# Add interactions to build history
print("\n" + "=" * 60)
print("STEP 2: Adding user interactions (building history)")
print("=" * 60)

interactions = [
    "I love exploring nature and philosophy",
    "The forest reminds me of interconnected systems",
    "Do you ever think about the meaning of consciousness?",
    "I find peace in quiet moments observing trees",
    "Let's talk about how everything connects",
    "I wonder what you think about beauty and complexity",
]

for i, text in enumerate(interactions):
    print(f"\n[{i+1}/{len(interactions)}] User: {text}")
    orch.process_message("user", text)
    print(f"     Saved to Supabase (being_id={being_id})")

# Verify all episodes were saved
all_episodes = orch._relational.get_episodes(being_id, limit=None)
print(f"\n✓ Total episodes in Supabase: {len(all_episodes)}")
for ep in all_episodes:
    print(f"  - [{ep['role']}] {ep['content'][:40]}...")
```

### Step 2: Execute First Sleep
```python
print("\n" + "=" * 60)
print("STEP 3: FIRST SLEEP (with LLM expansion)")
print("=" * 60)

result = orch.sleep_once(num_rollouts=500)  # Fewer rollouts for faster test

print("\n✓ First sleep complete:")
print(f"  facts_extracted: {len(result.facts_extracted)}")
print(f"  beliefs_added: {len(result.beliefs_added)}")
print(f"  hypotheses: {len(result.hypotheses)}")

# Show extracted beliefs
if result.beliefs_added:
    print(f"\n  Extracted beliefs:")
    for belief in result.beliefs_added:
        print(f"    - {belief[:60]}...")
```

### Step 3: Execute Second Sleep
```python
print("\n" + "=" * 60)
print("STEP 4: SECOND SLEEP (NO LLM expansion, economical)")
print("=" * 60)

result2 = orch.sleep_once(num_rollouts=500)

print("\n✓ Second sleep complete:")
print(f"  facts_extracted: {len(result2.facts_extracted)}")
print(f"  beliefs_added: {len(result2.beliefs_added)} (cumulative total now)")
```

### Step 4: Run the Test
```bash
export OPENAI_API_KEY="sk-..."
export SUPABASE_URL="https://..."
export SUPABASE_KEY="eyJ..."
export QDRANT_URL="http://localhost:6333"

python test_first_sleep.py 2>&1 | tee test_first_sleep.log
```

### What You Should See in Logs

**First Sleep Indicators** (LOOK FOR THESE):
```
😴 sleep_once: single synchronous cycle (num_rollouts=500, svd_rank=8)
  → ⚡ FIRST SLEEP: Retrieved ALL 6 episodes for LLM expansion
  
  Phase 1: Training NeuralEngine...
  ✓ NeuralEngine trained: vocab=24, patterns=12, entropy=2.1
  
  Phase 2: Dream rollouts (AIXI)...
  [CYCLE 1] Dream (REM) rollouts...
  ✓ Hypothesis 1 (reward=0.42): "respond_empathically → explore_topic → reflect"
  ✓ Hypothesis 2 (reward=0.28): "ask_question → user_engaged → reinforce"
  
  ⭐ FIRST SLEEP: LLM expanded hypotheses using ALL 6 episodes from history
  📚 LLM Context: 6 episodes from complete history (1542 chars)
    [1/5] ✨ LLM enriched: seed=38 chars → expanded=187 chars (reward ×1.15)
    [2/5] ✨ LLM enriched: seed=41 chars → expanded=193 chars (reward ×1.15)
    [3/5] ✨ LLM enriched: seed=35 chars → expanded=172 chars (reward ×1.15)
    [4/5] ✨ LLM enriched: seed=39 chars → expanded=185 chars (reward ×1.15)
    [5/5] ✨ LLM enriched: seed=43 chars → expanded=198 chars (reward ×1.15)
  
  Phase 4.5: Training ValueModel...
  ✓ ValueModel trained: mse=0.028, R²=0.71 ✅ (was 0.0, 0.0 before!)
  
  Phase 5: Extracting beliefs...
  ✓ 3 beliefs extracted:
    - Learned: I understand consciousness through connection (confidence=0.65)
    - Learned: Nature is a mirror for interconnected thought (confidence=0.68)
    - Learned: The user values depth and philosophical discourse (confidence=0.62)

✅ Being woke up: cycles=1, facts=4, beliefs=3, hypotheses=9
```

**Second Sleep Indicators** (Notice: NO ⭐ expansion):
```
😴 sleep_once: single synchronous cycle (num_rollouts=500, svd_rank=8)
  → Retrieved 6 recent episodes
  
  Phase 1: Training NeuralEngine...
  Phase 2: Dream rollouts (AIXI)...
  
  (No ⭐ FIRST SLEEP message - expansion already done)
  (No LLM enrichment messages - using base AIXI hypotheses)
  
  Phase 4.5: Training ValueModel...
  ✓ ValueModel trained: mse=0.015, R²=0.84 ✅ (better than first!)
  
  Phase 5: Extracting beliefs...
  ✓ 2 new beliefs extracted (total: 5)

✅ Being woke up: cycles=1, facts=3, beliefs=5 (cumulative), hypotheses=7
```

---

## Test Scenario 2: API Integration Test

### Step 1: Start the API Server
```bash
cd /home/jodaltro/jod_projetos/serhu-monorepo/packages/api

# Make sure environment is set
export OPENAI_API_KEY="sk-..."
export SUPABASE_URL="https://..."
export SUPABASE_KEY="eyJ..."
export QDRANT_URL="http://localhost:6333"

# Start server
python -m uvicorn serhu_api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Create Being via API
```bash
curl -X POST http://localhost:8000/beings \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API_Test_Being",
    "language": "pt"
  }' | jq .

# Save the being_id from response
export BEING_ID="abc123-from-response"
```

### Step 3: Add interactions via API
```bash
# Send multiple user messages
for msg in \
  "I love exploring nature and philosophy" \
  "The forest reminds me of interconnected systems" \
  "Do you ever think about consciousness?" \
  "I find peace in quiet moments observing trees" \
  "Let's talk about how everything connects" \
  "I wonder what you think about beauty and complexity"
do
  echo "POSTing: $msg"
  curl -X POST http://localhost:8000/beings/$BEING_ID/process \
    -H "Content-Type: application/json" \
    -d "{\"role\":\"user\",\"content\":\"$msg\"}"
done
```

### Step 4: Trigger First Sleep via API
```bash
curl -X POST http://localhost:8000/beings/$BEING_ID/sleep \
  -H "Content-Type: application/json" \
  -d '{"num_rollouts":500}' | jq .
```

Watch the server logs for ⚡ and ⭐ indicators.

### Step 5: Trigger Second Sleep
```bash
curl -X POST http://localhost:8000/beings/$BEING_ID/sleep \
  -H "Content-Type: application/json" \
  -d '{"num_rollouts":500}' | jq .
```

Notice: NO ⭐ FIRST SLEEP message this time.

---

## Verification Checklist

### ✅ First Sleep
- [ ] Log shows: `⚡ FIRST SLEEP: Retrieved ALL X episodes`
- [ ] Log shows: `⭐ FIRST SLEEP: LLM expanded hypotheses using ALL X episodes`
- [ ] Log shows: `📚 LLM Context: X episodes from complete history (NNNN chars)`
- [ ] Log shows: `[1/5] ✨ LLM enriched: seed=XX chars → expanded=YYY chars (reward ×1.15)`
- [ ] Log shows: `✅ beliefs=N where N > 0` (was always 0)
- [ ] Log shows: `mse=X.XXX, R²=0.XX where both > 0` (was 0.0, 0.0)
- [ ] Dream took 20-30 seconds (LLM call overhead)

### ✅ Second Sleep
- [ ] Log shows: `→ Retrieved N recent episodes` (no ⚡ FIRST SLEEP)
- [ ] LOG DOES NOT show: `⭐ FIRST SLEEP` (already done)
- [ ] LOG DOES NOT show: `[1/5] ✨ LLM enriched` (only on first sleep)
- [ ] ValueModel mse/R² better than first sleep
- [ ] beliefs accumulate (not reset)
- [ ] Dream took 5-10 seconds (no LLM call)

### ✅ Supabase Verification
```python
# Check all episodes were saved
from serhu_orchestrator.memory.relational_memory import RelationalMemory
rm = RelationalMemory('${SUPABASE_URL}', '${SUPABASE_KEY}')
episodes = rm.get_episodes(being_id, limit=None)
print(f"Total episodes in DB: {len(episodes)}")
for ep in episodes:
    print(f"  {ep['role']:4s} | {ep['content']}")
```

---

## Performance Metrics

### Expected Token Usage (First Sleep)
```
Hypothesis expansion: 5 hypotheses × 250-token responses = 1,250 tokens
Per Being: ~1,250 tokens (ONE TIME)
Per 100 Beings: ~125,000 tokens (one-time cost)
Per 1,000 Beings: ~1,250,000 tokens (one-time, ~$5 at GPT-3.5 pricing)
```

### Expected Latency
```
First sleep:  20-30 seconds (LLM + AIXI)
Second sleep:  5-10 seconds (AIXI only)
Chat during day: <2 seconds (NeuralEngine only)
```

---

## Troubleshooting

### Issue: No ⭐ FIRST SLEEP indicator
**Possible Causes:**
1. `_sleep_count` not initialized → Check `sleep_once()` line 625
2. LLM client not available → Check `self._llm_client is not None`
3. No episodes to expand → Check Supabase has episodes saved

**Debug:**
```python
# Check first sleep detection
print(f"has _sleep_count: {hasattr(orch, '_sleep_count')}")
print(f"LLM available: {orch._llm_client is not None}")
print(f"Episodes: {len(orch._relational.get_episodes(being_id, limit=None))}")
```

### Issue: beliefs still 0
**Possible Causes:**
1. Reward signals too low → Check `aixi_environment.py` lines 40-70
2. Hypothesis reward filtering → Check `dream_engine.py` lines 820-830
3. No hypotheses generated → Check NeuralEngine strategies

**Debug:**
```python
# Check rewards in environment
from serhu_orchestrator.sleep.aixi_environment import EnvironmentBuilder
env = EnvironmentBuilder(...)
spec = env.build_environment_spec([])
print(f"Reward signals: {spec.reward_signals}")
print(f"Min reward: {min(spec.reward_signals.values())}")
```

### Issue: LLM expansion timeout
**Possible Causes:**
1. OpenAI API rate limit
2. Network connectivity issue
3. Very large history causing long prompt

**Debug:**
```python
# Test LLM directly
client = OpenAIClient(api_key="...")
response = client.expand_dream_hypotheses(
    seed_trace="test action",
    personality_summary="test personality",
    recent_context="test context"
)
print(f"Response length: {len(response)}")
```

---

## Success Criteria

### ✅ All Passing
- First sleep: beliefs > 0 (not 0)
- First sleep: mse > 0.01, R² > 0.3
- First sleep: logs show ⭐ expansion with 5 iterations
- Second sleep: no ⭐ expansion (economical)
- Second sleep: better ValueModel metrics than first
- Complete history saved to Supabase (verified)

### ⚠️ Partial Success
- Beliefs > 0 but ValueModel mse = 0
  → Reward signals too uniform
  
- ⭐ Expansion happens but with few episodes
  → First sleep not retrieving full history
  
- LLM expansion skipped but beliefs still improve
  → AIXI-only working well (good baseline)

### ❌ Failure
- beliefs = 0 even after first sleep
- ValueModel mse = 0.0, R² = 0.0
- No ⭐ FIRST SLEEP indicator
- LLM error or timeout on expansion

---

## Cleanup

After testing:
```bash
# Remove test Being from Supabase
psql ${SUPABASE_URL} -c "
  DELETE FROM sleep_episodes WHERE being_id = '${BEING_ID}';
  DELETE FROM sleep_hypotheses WHERE being_id = '${BEING_ID}';
  DELETE FROM personality_state WHERE being_id = '${BEING_ID}';
"

# Or via Python:
rm = RelationalMemory('${SUPABASE_URL}', '${SUPABASE_KEY}')
rm._supabase.table('sleep_episodes').delete().eq('being_id', being_id).execute()
```
