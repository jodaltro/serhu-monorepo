"""Unit tests for DreamEngine and SleepCycle."""

import pytest

from serhu_orchestrator.sleep.dream_engine import DreamEngine, Hypothesis
from serhu_orchestrator.sleep.sleep_cycle import SleepCycle, SleepResult
from serhu_orchestrator.sleep.value_model import ValueModel
from serhu_orchestrator.personality.types import PersonalityState


# ---------------------------------------------------------------------------
# DreamEngine tests
# ---------------------------------------------------------------------------


class TestDreamEngineRollouts:
    """Tests for AIXI-inspired dream rollouts."""

    def test_returns_correct_number_of_hypotheses(self):
        engine = DreamEngine(seed=42)
        history = [{"content": "hello"}, {"content": "world"}]
        personality = [0.5] * 72
        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=100, top_k=5
        )
        assert len(results) == 5

    def test_returns_hypothesis_objects(self):
        engine = DreamEngine(seed=42)
        history = [{"content": "test"}]
        personality = [0.5] * 72
        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=10, top_k=3
        )
        for h in results:
            assert isinstance(h, Hypothesis)
            assert isinstance(h.action, str)
            assert isinstance(h.reward, float)
            assert isinstance(h.complexity, float)

    def test_hypotheses_sorted_by_reward_descending(self):
        engine = DreamEngine(seed=42)
        history = [{"content": "hello world"}]
        personality = [0.5] * 72
        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=100, top_k=10
        )
        for i in range(len(results) - 1):
            assert results[i].reward >= results[i + 1].reward

    def test_deterministic_with_seed(self):
        history = [{"content": "consistency check"}]
        personality = [0.5] * 72
        r1 = DreamEngine(seed=123).perform_dream_rollouts(
            history, personality, num_rollouts=50, top_k=5
        )
        r2 = DreamEngine(seed=123).perform_dream_rollouts(
            history, personality, num_rollouts=50, top_k=5
        )
        assert [h.action for h in r1] == [h.action for h in r2]
        assert [h.reward for h in r1] == [h.reward for h in r2]

    def test_empty_history_does_not_crash(self):
        engine = DreamEngine(seed=42)
        results = engine.perform_dream_rollouts(
            [], [0.5] * 72, num_rollouts=10, top_k=3
        )
        assert len(results) == 3

    def test_personality_influences_exploration(self):
        history = [{"content": "explore this"}]
        # High openness personality (index 20 = inquisitiveness in HEXACO)
        high_open = [0.5] * 72
        high_open[20] = 1.0
        low_open = [0.5] * 72
        low_open[20] = 0.0

        r_high = DreamEngine(seed=42).perform_dream_rollouts(
            history, high_open, num_rollouts=200, top_k=50
        )
        r_low = DreamEngine(seed=42).perform_dream_rollouts(
            history, low_open, num_rollouts=200, top_k=50
        )
        # High-openness should produce more exploration-based hypotheses
        explore_high = sum(1 for h in r_high if "hypothesis_about:" in h.action)
        explore_low = sum(1 for h in r_low if "hypothesis_about:" in h.action)
        assert explore_high >= explore_low


class TestDreamPruning:
    """Tests for SVD rank-reduction consolidation."""

    def test_preserves_vector_length(self):
        vector = [0.5] * 72
        result = DreamEngine.dream_pruning(vector, target_rank=8)
        assert len(result) == 72

    def test_values_remain_in_bounds(self):
        vector = [0.1 * i for i in range(20)]
        result = DreamEngine.dream_pruning(vector, target_rank=4)
        for v in result:
            assert 0.0 <= v <= 1.0

    def test_empty_vector_returns_empty(self):
        result = DreamEngine.dream_pruning([], target_rank=4)
        assert result == []

    def test_target_rank_larger_than_vector_returns_copy(self):
        vector = [0.3, 0.6, 0.9]
        result = DreamEngine.dream_pruning(vector, target_rank=10)
        assert result == vector

    def test_consolidation_changes_noisy_values(self):
        # A vector with noise should be smoothed
        vector = [0.5, 0.51, 0.49, 0.5, 0.52, 0.48, 0.5, 0.5,
                  0.1, 0.9, 0.1, 0.9, 0.1, 0.9, 0.1, 0.9]
        result = DreamEngine.dream_pruning(vector, target_rank=2)
        assert len(result) == len(vector)
        # The result should be different from input (smoothed)
        assert result != vector


# ---------------------------------------------------------------------------
# SleepCycle tests
# ---------------------------------------------------------------------------


class TestSleepCycleSemantization:
    """Tests for the semantization phase of the sleep cycle."""

    def _make_state(self) -> PersonalityState:
        return PersonalityState(being_id="semantize-test", name="Tester")

    def test_extracts_facts_from_frequent_words(self):
        episodes = [
            {"content": "I love painting landscapes"},
            {"content": "Painting is my passion"},
            {"content": "I painted something today"},
        ]
        cycle = SleepCycle()
        facts = cycle._semantize(episodes, self._make_state())
        assert any("painting" in f.lower() for f in facts)

    def test_no_facts_from_infrequent_words(self):
        episodes = [
            {"content": "One unique word here"},
            {"content": "Another different sentence"},
        ]
        cycle = SleepCycle()
        facts = cycle._semantize(episodes, self._make_state())
        # No word appears ≥2 times (except short words ≤4 chars)
        assert len(facts) == 0

    def test_empty_episodes_produce_no_facts(self):
        cycle = SleepCycle()
        facts = cycle._semantize([], self._make_state())
        assert facts == []


class TestSleepCycleRun:
    """Tests for the full sleep cycle."""

    def _make_state(self) -> PersonalityState:
        return PersonalityState(being_id="sleep-test-001", name="Dreamer")

    def test_full_cycle_returns_result(self):
        state = self._make_state()
        episodes = [
            {"content": "Hello there"},
            {"content": "I love music and music is great"},
            {"content": "Music makes me happy"},
        ]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))
        new_state, result = cycle.run(state, episodes, num_rollouts=50, svd_rank=4)

        assert isinstance(result, SleepResult)
        assert isinstance(new_state, PersonalityState)
        assert len(result.traits_before) == 72
        assert len(result.traits_after) == 72
        assert len(result.hypotheses) > 0

    def test_beliefs_are_added_after_sleep(self):
        state = self._make_state()
        assert state.core_beliefs == []
        episodes = [{"content": "The world is beautiful"}]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))
        new_state, result = cycle.run(state, episodes, num_rollouts=50)
        # Core beliefs should have been updated
        assert len(new_state.core_beliefs) > 0
        assert all("Learned:" in b for b in new_state.core_beliefs)

    def test_traits_before_and_after_differ(self):
        state = self._make_state()
        # Apply varied trait values so SVD has something to consolidate
        state.hexaco.sincerity = 0.9
        state.hexaco.creativity = 0.2
        state.tci_temperament.exploratory_excitability = 0.8
        state.tci_temperament.shyness = 0.3
        episodes = [
            {"content": f"Message number {i} about nature and beauty"}
            for i in range(20)
        ]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))
        _, result = cycle.run(state, episodes, num_rollouts=50, svd_rank=4)
        # SVD consolidation should modify at least some trait values
        assert result.traits_before != result.traits_after

    def test_flatten_traits_produces_72_dims(self):
        state = self._make_state()
        vector = SleepCycle._flatten_traits(state)
        # 24 HEXACO + 16 TCI-T + 13 TCI-C + 19 Schwartz = 72
        assert len(vector) == 72

    def test_apply_consolidated_traits_respects_bounds(self):
        state = self._make_state()
        # Some values out of normal range
        consolidated = [1.5] * 24 + [-0.1] * 16 + [0.5] * 13 + [0.7] * 19
        state = SleepCycle._apply_consolidated_traits(state, consolidated)
        # Check that clamping was applied
        assert state.hexaco.sincerity == 1.0  # clamped from 1.5
        assert state.tci_temperament.exploratory_excitability == 0.0  # clamped from -0.1

    def test_run_returns_cycles_completed_one(self):
        state = self._make_state()
        episodes = [{"content": "Hello"}]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))
        _, result = cycle.run(state, episodes, num_rollouts=10, svd_rank=4)
        assert result.cycles_completed == 1


# ---------------------------------------------------------------------------
# Continuous Sleep tests
# ---------------------------------------------------------------------------


class TestSleepCycleContinuous:
    """Tests for the continuous (infinite AIXI) sleep mode."""

    def _make_state(self) -> PersonalityState:
        return PersonalityState(being_id="continuous-test", name="Dreamer")

    def test_continuous_runs_multiple_cycles(self):
        """Continuous mode runs more than one cycle before stop."""
        state = self._make_state()
        episodes = [
            {"content": "I love music and music is great"},
            {"content": "Music makes me happy"},
        ]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        # Stop after 3 cycles via on_cycle callback
        def stop_after_3(cycle_num, _state):
            if cycle_num >= 3:
                cycle.request_stop()

        new_state, result = cycle.run_continuous(
            state, episodes, num_rollouts=10, svd_rank=4, on_cycle=stop_after_3
        )

        assert result.cycles_completed == 3
        assert isinstance(new_state, PersonalityState)
        assert len(result.traits_before) == 72
        assert len(result.traits_after) == 72

    def test_continuous_accumulates_beliefs(self):
        """Each cycle adds beliefs to the accumulated result."""
        state = self._make_state()
        episodes = [{"content": "The world is beautiful"}]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        def stop_after_2(cycle_num, _state):
            if cycle_num >= 2:
                cycle.request_stop()

        new_state, result = cycle.run_continuous(
            state, episodes, num_rollouts=10, svd_rank=4, on_cycle=stop_after_2
        )

        assert result.cycles_completed == 2
        # Beliefs accumulate across cycles (extend, not replace)
        assert len(result.beliefs_added) >= 1

    def test_continuous_stops_immediately_if_pre_stopped(self):
        """If stop is requested before starting, zero cycles run."""
        state = self._make_state()
        episodes = [{"content": "test"}]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))
        cycle.request_stop()  # Pre-stop

        _, result = cycle.run_continuous(
            state, episodes, num_rollouts=10, svd_rank=4
        )

        assert result.cycles_completed == 0

    def test_continuous_semantizes_once(self):
        """Semantization only occurs once at the start."""
        state = self._make_state()
        episodes = [
            {"content": "I love music and music is great"},
            {"content": "Music makes me happy"},
        ]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        def stop_after_2(cycle_num, _state):
            if cycle_num >= 2:
                cycle.request_stop()

        _, result = cycle.run_continuous(
            state, episodes, num_rollouts=10, svd_rank=4, on_cycle=stop_after_2
        )

        # Facts should be extracted (from semantization)
        assert len(result.facts_extracted) >= 1
        assert any("music" in f.lower() for f in result.facts_extracted)

    def test_request_stop_and_stop_requested(self):
        """request_stop() sets the stop flag; stop_requested reflects it."""
        cycle = SleepCycle()
        assert cycle.stop_requested is False
        cycle.request_stop()
        assert cycle.stop_requested is True

    def test_continuous_from_thread_with_stop(self):
        """Continuous mode can be stopped from another thread."""
        import threading
        import time

        state = self._make_state()
        episodes = [{"content": "Deep dreaming"}]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        result_holder: list[tuple[PersonalityState, SleepResult]] = []

        def worker():
            r = cycle.run_continuous(
                state, episodes, num_rollouts=10, svd_rank=4
            )
            result_holder.append(r)

        t = threading.Thread(target=worker)
        t.start()

        # Let it run for a short while
        time.sleep(0.3)
        cycle.request_stop()
        t.join(timeout=5.0)

        assert len(result_holder) == 1
        _, result = result_holder[0]
        assert result.cycles_completed >= 1


# ---------------------------------------------------------------------------
# ValueModel integration tests
# ---------------------------------------------------------------------------


class TestSleepCycleValueModel:
    """Tests for ValueModel training during sleep cycle."""

    def _make_state(self) -> PersonalityState:
        return PersonalityState(being_id="vm-test-001", name="VMTester")

    def test_run_produces_value_model(self):
        """Single-shot run should produce a trained ValueModel."""
        state = self._make_state()
        episodes = [
            {"content": "I love music and music is great"},
            {"content": "Music makes me happy"},
        ]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))
        _, result = cycle.run(state, episodes, num_rollouts=50, svd_rank=4)

        assert result.value_model is not None
        assert isinstance(result.value_model, ValueModel)
        assert result.value_model.is_trained
        assert result.value_model.version != ""

    def test_value_model_has_metrics(self):
        """The trained ValueModel should have quality metrics."""
        state = self._make_state()
        episodes = [{"content": "Stars are beautiful"}]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))
        _, result = cycle.run(state, episodes, num_rollouts=50, svd_rank=4)

        if result.value_model is not None:
            assert "mse" in result.value_model.metrics
            assert "samples" in result.value_model.metrics
            assert "r_squared" in result.value_model.metrics

    def test_value_model_can_predict(self):
        """After sleep, the ValueModel should be able to predict rewards."""
        state = self._make_state()
        episodes = [
            {"content": "I love music and music is great"},
            {"content": "Music makes me happy"},
        ]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))
        _, result = cycle.run(state, episodes, num_rollouts=50, svd_rank=4)

        if result.value_model is not None:
            pred = result.value_model.predict([0.5] * 72, "explore_topic")
            assert isinstance(pred, float)

    def test_continuous_produces_value_model(self):
        """Continuous mode should produce a ValueModel."""
        state = self._make_state()
        episodes = [
            {"content": "I love music and music is great"},
            {"content": "Music makes me happy"},
        ]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        def stop_after_2(cycle_num, _state):
            if cycle_num >= 2:
                cycle.request_stop()

        _, result = cycle.run_continuous(
            state, episodes, num_rollouts=10, svd_rank=4, on_cycle=stop_after_2
        )

        assert result.value_model is not None
        assert result.value_model.is_trained

    def test_sleep_result_value_model_default_none(self):
        """SleepResult should default value_model to None."""
        result = SleepResult()
        assert result.value_model is None
