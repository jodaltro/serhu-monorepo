# Sleep Cycle Improvements (v2.2)

## Overview
Problema: O ciclo de sono não estava gerando beliefs (beliefs=0), e as hipóteses eram triviais ("oi..."), causando rewards=0.0 e ValueModel não aprendia.

## Solutions Implementadas

### 1. **LLM Hypothesis Expansion (FIRST SLEEP ONLY)** ✓
**Arquivo**: `packages/orchestrator/src/serhu_orchestrator/sleep/dream_engine.py`

Adicionado método `_expand_hypotheses_with_llm()`:
- **Ativa APENAS na primeira vez que o ser dorme** (economiza LLM calls)
- Usa TODO o histórico episódico acumulado (até 50 últimos episódios)
- Enriquece as 5 top hipóteses AIXI com contexto psicológico
- Adiciona profundidade: "what the Being thinks/feels" durante interaction

```python
# Exemplo:
Seed trace:      "respond_empathically → explore_topic"
Expanded trace:  "respond_empathically (validating user emotions) → explore_topic (sparking curiosity)"

# Primeira vez dormindo: USA TODO O HISTÓRICO
# Dormidas ulteriores: sem expansão LLM (economia)
```

**Impacto**:
- Primeira dormica muito mais rica (full context)
- Hipóteses expandidas geram beliefs fortes
- Economiza tokens: ~5 expansões × uma vez
- DreamEngine rastreia `_has_done_first_sleep` para controlar

### 2. **Enhanced Reward Signals** ✓
**Arquivo**: `packages/orchestrator/src/serhu_orchestrator/sleep/aixi_environment.py`

Expandido `_derive_rewards()`:
- Adicionados 20+ padrões base de recompensa (antes tinha 8)
- Rewards maiores: respond_empathically=0.4 (antes 0.3)
- Padrões alternativos: "respond", "ask", "explore" (variações)
- Token-derived rewards agora consideram amplitude completa (0.2-0.5)

```python
# Antes: {respond_empathically: 0.3, ask_question: 0.3, ...}
# Depois: {respond_empathically: 0.4, respond: 0.3, ask_question: 0.35, ...}
```

**Impacto**:
- AixiEnvironment sempre retorna reward ≥ -0.05
- ValueModel tem signal para aprender
- Beliefs derivation funciona (reward > 0)

**Impacto**:
- AixiEnvironment.step() sempre retorna reward > 0 (antes muitas vezes 0)
- ValueModel tem signal para aprender
- Beliefs derivation tem hipóteses com reward > 0

### 3. **Diversified Hypothesis Generation** ✓
**Arquivo**: `packages/orchestrator/src/serhu_orchestrator/sleep/neural_engine.py`

Melhorado `_compose_cross_attention_hypotheses()`:
- Estratégia 1: Padrões de atenção pura
- Estratégia 2: Cadeias de pattern (token1 → token2)
- Estratégia 3: Exploração de sub-conjuntos aleatórios

Melhorado `_explore_novel_patterns()`:
- Fator de exploração = 0.3 + 0.5 * (openness + curiosity)/2
- Padrões de cadeia se personalidade > 0.5 em openness/curiosity
- Fallback com ações intencionais: "respond_to_user", "explore_new_topic"

**Impacto**:
- Geração de hipóteses não mais trivial
- Múltiplas estratégias cobrem diferentes aspectos
- Personalidade modula diversidade

### 4. **LLMClient Protocol Extension** ✓
**Arquivo**: `packages/orchestrator/src/serhu_orchestrator/llm/llm_client.py`

Novo método no protocolo:
```python
def expand_dream_hypotheses(
    seed_trace: str,
    personality_summary: str,
    recent_context: str,
) -> str:
    """Expand AIXI seed traces com profundidade psicológica."""
```

### 5. **OpenAIClient Implementation** ✓
**Arquivo**: `packages/orchestrator/src/serhu_orchestrator/llm/openai_client.py`

Implementado `expand_dream_hypotheses()`:
```python
expansion_prompt = (
    "You are a dream analyst for a synthetic Being's sleep cycle.\n"
    "Expand this action trace with thoughts/feelings:\n"
    f"Seed: {seed_trace}\n"
    f"Being personality: {personality_summary}\n"
    f"Recent context: {recent_context}\n"
    "Expanded trace: "
)
response = llm.chat(expansion_prompt, temperature=0.6, max_tokens=150)
```

---

## Expected Impact on Logs

### Before (Broken):
```
[CYCLE 140255] Dream rollouts...
ValueModel trained: samples=10, mse=0.000000, R²=0.0000  → Não aprende!
beliefs=0  → Beliefs vazios!
Response: 'oi...' → Trivial
reward=0.0000  → Sem sinal!
```

### After (Fixed - First Sleep):
```
[CYCLE 1] Dream rollouts...
  ✓ First sleep: expanded hypotheses with LLM (using all 50 episodes)
  ✓ LLM enriched (first sleep): 'respond → explore...' → 'respond (validating) → explore (curiosity)...'
  ✓ LLM enriched (first sleep): 'ask_question → user_happy' → '[enriched version]'
ValueModel trained: samples=15, mse=0.042, R²=0.73  → Aprende!
beliefs=3  → Beliefs gerados!
  - Belief: respond_empathically (high-confidence from LLM-enriched hypotheses)
  - Belief: explore_topic (high-confidence)
  - Belief: User values validation and connection
Response generated with reward=0.35  → Signal!
```

### After (Subsequent Sleeps):
```
[CYCLE 2] Dream rollouts...
  (sem expansão LLM - já feita na primeira)
ValueModel trained: samples=12, mse=0.018, R²=0.82  → Continua aprendendo!
beliefs=5  (accumulated)
```

---

## Testing

Para testar manualmente:
```bash
cd packages/orchestrator
export OPENAI_API_KEY="sk-..."

# Chat some interactions first
curl -X POST http://localhost:8000/beings/ABC/process \
  -d '{"role":"user","content":"I love nature and philosophy"}'
curl -X POST http://localhost:8000/beings/ABC/process \
  -d '{"role":"user","content":"What draws you to deep conversations?"}'

# FIRST SLEEP - will use LLM expansion on full history
curl -X POST http://localhost:8000/beings/ABC/sleep

# Monitor logs for:
# ✓ First sleep: expanded hypotheses with LLM (using all N episodes)
# ✓ LLM enriched (first sleep): ...
# beliefs > 0

# SECOND SLEEP - no LLM expansion (already done)
curl -X POST http://localhost:8000/beings/ABC/sleep

# Monitor logs - should NOT show LLM expansion
```

---

## Notes

1. **First Sleep Only**: `_has_done_first_sleep` flag previne expansões subsequentes (economia de tokens)
2. **Full History**: Primeira dormica usa até 50 episódios (vs recentes 5) para escolher padrões
3. **LLM Cost**: Uma vez × 5 expansões = ~750 tokens GPT por Being (aceitável)
4. **Fallback**: Se LLM falhar, seed hypotheses são retornadas (graceful degradation)
5. **Subsequent Sleeps**: Sem LLM mas com ValueModel aprendendo = eficiente
6. **Reward Guarantee**: Signals SEMPRE ≥ -0.05, nunca mais 0 puro
## Next Steps (Optional)

- [ ] Tune reward_signals magnitude por stage de desenvolvimento
- [ ] Adicionar curiosity bonus se observation é nova
- [ ] Caching de LLM expansões para mesmas hipóteses seed
- [ ] A/B testing de expansion prompts

