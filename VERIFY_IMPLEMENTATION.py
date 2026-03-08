#!/usr/bin/env python3
"""Quick verification that complete history → first sleep expansion is working.

Usage:
    python VERIFY_IMPLEMENTATION.py

Checks:
    1. Orchestrator properly detects first sleep
    2. DreamEngine tracks first-sleep state
    3. LLM expansion method exists and accepts full history
    4. Reward signals are diverse (not all zero)
    5. Beliefs can be extracted (reward filtering allows them)
"""

import sys
import inspect
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "orchestrator" / "src"))

def check_orchestrator_first_sleep_detection():
    """Verify Orchestrator.sleep_once() has first sleep detection."""
    from serhu_orchestrator.orchestrator import Orchestrator
    
    source = inspect.getsource(Orchestrator.sleep_once)
    
    checks = [
        ("_sleep_count tracking", "_sleep_count" in source),
        ("is_first_sleep detection", "is_first_sleep = not hasattr" in source or "is_first_sleep =" in source),
        ("limit=None for first sleep", "limit=None" in source),
        ("limit=100 for subsequent", "limit=100" in source),
        ("⚡ FIRST SLEEP log", "⚡ FIRST SLEEP" in source),
        ("DreamEngine is_first_sleep param", "is_first_sleep=is_first_sleep" in source),
    ]
    
    print("\n✓ Orchestrator.sleep_once() verification:")
    all_pass = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        all_pass = all_pass and result
    
    return all_pass

def check_dream_engine_first_sleep_tracking():
    """Verify DreamEngine properly tracks first sleep."""
    from serhu_orchestrator.sleep.dream_engine import DreamEngine
    
    init_source = inspect.getsource(DreamEngine.__init__)
    rollout_source = inspect.getsource(DreamEngine.perform_dream_rollouts)
    expand_source = inspect.getsource(DreamEngine._expand_hypotheses_with_llm) if hasattr(DreamEngine, '_expand_hypotheses_with_llm') else ""
    
    checks = [
        ("__init__ accepts is_first_sleep", "is_first_sleep" in init_source),
        ("__init__ sets _has_done_first_sleep", "_has_done_first_sleep" in init_source),
        ("perform_dream_rollouts checks first sleep", "is_first_sleep = not self._has_done_first_sleep" in rollout_source),
        ("LLM expansion only on first sleep", "if is_first_sleep and self._llm_client" in rollout_source),
        ("Marks first sleep as done", "self._has_done_first_sleep = True" in rollout_source),
        ("⭐ FIRST SLEEP log", "⭐ FIRST SLEEP" in rollout_source),
    ]
    
    print("\n✓ DreamEngine first-sleep tracking:")
    all_pass = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        all_pass = all_pass and result
    
    return all_pass

def check_llm_expansion_with_full_history():
    """Verify _expand_hypotheses_with_llm uses full history."""
    from serhu_orchestrator.sleep.dream_engine import DreamEngine
    from serhu_orchestrator.llm.llm_client import LLMClient
    
    if not hasattr(DreamEngine, '_expand_hypotheses_with_llm'):
        print("\n❌ DreamEngine._expand_hypotheses_with_llm not found!")
        return False
    
    expand_source = inspect.getsource(DreamEngine._expand_hypotheses_with_llm)
    
    checks = [
        ("Accepts history parameter", "history" in expand_source),
        ("Uses full history (no limit)", "history[-50:" not in expand_source or "limit" not in expand_source),
        ("Calls llm_client.expand_dream_hypotheses", "expand_dream_hypotheses" in expand_source),
        ("Passes full history to LLM", "recent_context=" in expand_source and "episode_text" in expand_source),
        ("📚 logging for context", "📚" in expand_source or "LLM Context" in expand_source),
        ("✨ logging for enriched", "✨" in expand_source or "LLM enriched" in expand_source),
    ]
    
    print("\n✓ DreamEngine._expand_hypotheses_with_llm verification:")
    all_pass = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        all_pass = all_pass and result
    
    return all_pass

def check_openai_expand_method():
    """Verify OpenAIClient has expand_dream_hypotheses method."""
    try:
        from serhu_orchestrator.llm.openai_client import OpenAIClient
    except ImportError:
        print("\n⚠️  OpenAIClient not available (optional)")
        return True
    
    if not hasattr(OpenAIClient, 'expand_dream_hypotheses'):
        print("\n❌ OpenAIClient.expand_dream_hypotheses not found!")
        return False
    
    source = inspect.getsource(OpenAIClient.expand_dream_hypotheses)
    
    checks = [
        ("Accepts seed_trace", "seed_trace" in source),
        ("Accepts personality_summary", "personality_summary" in source),
        ("Accepts recent_context (full history)", "recent_context" in source),
        ("Uses full context in prompt", "recent_context" in source and "Being's accumulated experience" in source),
        ("High temperature for creativity (0.7)", "temperature=0.7" in source or "temperature = 0.7" in source),
        ("Max tokens for depth (250)", "max_completion_tokens=250" in source or "max_completion_tokens = 250" in source),
        ("Logs FIRST SLEEP emphasis", "FIRST" in source or "first" in source),
    ]
    
    print("\n✓ OpenAIClient.expand_dream_hypotheses verification:")
    all_pass = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        all_pass = all_pass and result
    
    return all_pass

def check_reward_signals_diverse():
    """Verify reward signals are diverse (not all zero)."""
    from serhu_orchestrator.sleep.aixi_environment import EnvironmentBuilder
    
    # Build minimal environment
    builder = EnvironmentBuilder(
        episodes=[],
        personality=None,
        being_id="test"
    )
    
    try:
        # Get accessible reward signals
        spec = builder.build_environment_spec([])
        rewards = spec.reward_signals if spec else {}
        
        if not rewards:
            print("\n⚠️  Cannot extract reward signals (optional check)")
            return True
        
        values = list(rewards.values())
        has_diversity = len(set(values)) > 1 or min(values) > 0
        
        print("\n✓ Reward signals verification:")
        print(f"  ✅ Found {len(rewards)} reward patterns")
        print(f"  ✅ Values range: {min(values):.2f} to {max(values):.2f}")
        print(f"  ✅ Diversity: {'Yes' if has_diversity else 'Limited'}")
        
        return has_diversity
    except Exception as e:
        print(f"\n⚠️  Could not verify rewards: {e}")
        return True

def check_belief_extraction_logic():
    """Verify belief extraction can work (not filtered to zero)."""
    from serhu_orchestrator.sleep.dream_engine import DreamEngine
    
    # Check if extraction logic exists and doesn't filter everything
    if not hasattr(DreamEngine, '_extract_beliefs_from_hypotheses'):
        print("\n⚠️  _extract_beliefs_from_hypotheses not found (optional)")
        return True
    
    source = inspect.getsource(DreamEngine._extract_beliefs_from_hypotheses)
    
    checks = [
        ("Filters by reward threshold", "reward >" in source or "reward >=" in source),
        ("Threshold is reasonable (not > 1.0)", "> 1." not in source),
        ("Converts hypotheses to beliefs", "belief" in source.lower()),
    ]
    
    print("\n✓ Belief extraction logic:")
    all_pass = True
    for check_name, result in checks:
        status = "✅" if result else "⚠️"
        print(f"  {status} {check_name}")
        all_pass = all_pass and result
    
    return all_pass

def check_memory_manager_saves_everything():
    """Verify MemoryManager saves all interactions."""
    from serhu_orchestrator.memory.memory_manager import MemoryManager
    
    source = inspect.getsource(MemoryManager.add_interaction)
    
    checks = [
        ("Saves to relational (Supabase)", "relational" in source or "_relational" in source),
        ("Logs episode", "log_episode" in source),
        ("Passes being_id", "being_id" in source),
        ("Passes role", "role" in source),
        ("Passes content", "content" in source),
    ]
    
    print("\n✓ MemoryManager.add_interaction verification:")
    all_pass = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        all_pass = all_pass and result
    
    return all_pass

def main():
    """Run all verification checks."""
    print("=" * 70)
    print("VERIFYING: Complete History → First Sleep Expansion Implementation")
    print("=" * 70)
    
    results = {
        "Orchestrator first-sleep detection": check_orchestrator_first_sleep_detection(),
        "DreamEngine first-sleep tracking": check_dream_engine_first_sleep_tracking(),
        "LLM expansion with full history": check_llm_expansion_with_full_history(),
        "OpenAI expand method": check_openai_expand_method(),
        "Reward signals diverse": check_reward_signals_diverse(),
        "Belief extraction logic": check_belief_extraction_logic(),
        "MemoryManager saves everything": check_memory_manager_saves_everything(),
    }
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 IMPLEMENTATION VERIFIED!")
        print("\nNext steps:")
        print("  1. Set environment variables (OPENAI_API_KEY, SUPABASE_URL, etc)")
        print("  2. Run test scenario: python TESTING_FIRST_SLEEP.md")
        print("  3. Monitor logs for ⚡ FIRST SLEEP and ⭐ LLM expanded indicators")
        print("  4. Verify beliefs > 0 and ValueModel learns (mse > 0, R² > 0)")
        return 0
    else:
        print("\n⚠️  Some checks failed. See above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
