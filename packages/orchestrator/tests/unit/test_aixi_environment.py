"""Unit tests for AIXI Environment – RL-like environment for dream rollouts."""

import pytest

from serhu_orchestrator.sleep.aixi_environment import (
    AixiEnvironment,
    EnvironmentBuilder,
    EnvironmentSpec,
)
from serhu_orchestrator.sleep.neural_engine import NeuralEngine
from serhu_orchestrator.sleep.dream_engine import DreamEngine, Hypothesis
from serhu_orchestrator.sleep.sleep_cycle import SleepCycle, SleepResult
from serhu_orchestrator.personality.types import PersonalityState


# ---------------------------------------------------------------------------
# EnvironmentSpec tests
# ---------------------------------------------------------------------------


class TestEnvironmentSpec:
    """Tests for the EnvironmentSpec dataclass."""

    def test_default_spec(self):
        spec = EnvironmentSpec()
        assert spec.actions == []
        assert spec.observations == []
        assert spec.reward_signals == {}
        assert spec.transition_weights == {}
        assert spec.horizon == 10
        assert spec.gamma == 0.95

    def test_custom_spec(self):
        spec = EnvironmentSpec(
            actions=["explore", "ask"],
            observations=["happy", "curious"],
            reward_signals={"explore": 0.5},
            horizon=15,
            gamma=0.9,
        )
        assert len(spec.actions) == 2
        assert len(spec.observations) == 2
        assert spec.reward_signals["explore"] == 0.5
        assert spec.horizon == 15
        assert spec.gamma == 0.9


# ---------------------------------------------------------------------------
# AixiEnvironment tests
# ---------------------------------------------------------------------------


class TestAixiEnvironment:
    """Tests for the RL-like AixiEnvironment."""

    def _make_spec(self) -> EnvironmentSpec:
        return EnvironmentSpec(
            actions=["explore_topic", "ask_question", "reflect_on_self"],
            observations=["user_happy", "user_curious", "silence"],
            reward_signals={
                "explore": 0.3,
                "ask": 0.2,
                "user_happy": 0.4,
                "silence": -0.1,
            },
            transition_weights={
                "explore_topic": [
                    ("user_curious", 0.5),
                    ("user_happy", 0.3),
                    ("silence", 0.2),
                ],
                "ask_question": [
                    ("user_curious", 0.4),
                    ("user_happy", 0.4),
                    ("silence", 0.2),
                ],
            },
            horizon=5,
            gamma=0.95,
        )

    def test_reset_returns_observation(self):
        env = AixiEnvironment(self._make_spec(), [0.5] * 72, seed=42)
        obs = env.reset()
        assert obs in {"user_happy", "user_curious", "silence"}

    def test_step_returns_tuple(self):
        env = AixiEnvironment(self._make_spec(), [0.5] * 72, seed=42)
        env.reset()
        obs, reward, done, info = env.step("explore_topic")
        assert isinstance(obs, str)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)

    def test_step_transitions_with_model(self):
        env = AixiEnvironment(self._make_spec(), [0.5] * 72, seed=42)
        env.reset()
        obs, _, _, _ = env.step("explore_topic")
        # Should get one of the transition observations
        assert obs in {"user_curious", "user_happy", "silence"}

    def test_step_done_at_horizon(self):
        spec = self._make_spec()
        spec.horizon = 3
        env = AixiEnvironment(spec, [0.5] * 72, seed=42)
        env.reset()
        for i in range(3):
            _, _, done, _ = env.step("explore_topic")
        assert done is True

    def test_step_not_done_before_horizon(self):
        spec = self._make_spec()
        spec.horizon = 5
        env = AixiEnvironment(spec, [0.5] * 72, seed=42)
        env.reset()
        _, _, done, _ = env.step("explore_topic")
        assert done is False

    def test_reward_from_signals(self):
        spec = EnvironmentSpec(
            actions=["explore_topic"],
            observations=["user_happy"],
            reward_signals={"explore": 0.5, "user_happy": 0.3},
            transition_weights={
                "explore_topic": [("user_happy", 1.0)],
            },
            horizon=5,
        )
        env = AixiEnvironment(spec, [0.5] * 72, seed=42)
        env.reset()
        _, reward, _, _ = env.step("explore_topic")
        # Should include rewards from both "explore" (in action) and "user_happy" (in obs)
        assert reward > 0.0

    def test_personality_modulates_reward(self):
        spec = EnvironmentSpec(
            actions=["explore_novel"],
            observations=["user_curious"],
            reward_signals={},
            transition_weights={
                "explore_novel": [("user_curious", 1.0)],
            },
            horizon=5,
        )
        # High openness + curiosity
        high_vec = [0.5] * 72
        high_vec[20] = 1.0  # openness
        high_vec[24] = 1.0  # curiosity

        low_vec = [0.5] * 72
        low_vec[20] = 0.0
        low_vec[24] = 0.0

        env_high = AixiEnvironment(spec, high_vec, seed=42)
        env_high.reset()
        _, r_high, _, _ = env_high.step("explore_novel")

        env_low = AixiEnvironment(spec, low_vec, seed=42)
        env_low.reset()
        _, r_low, _, _ = env_low.step("explore_novel")

        assert r_high > r_low

    def test_reset_resets_step_count(self):
        env = AixiEnvironment(self._make_spec(), [0.5] * 72, seed=42)
        env.reset()
        env.step("explore_topic")
        env.step("ask_question")
        env.reset()
        _, _, done, info = env.step("explore_topic")
        assert info["step"] == 1
        assert done is False

    def test_deterministic_with_seed(self):
        spec = self._make_spec()
        env1 = AixiEnvironment(spec, [0.5] * 72, seed=42)
        env2 = AixiEnvironment(spec, [0.5] * 72, seed=42)

        obs1 = env1.reset()
        obs2 = env2.reset()
        assert obs1 == obs2

        result1 = env1.step("explore_topic")
        result2 = env2.step("explore_topic")
        assert result1[0] == result2[0]  # observation
        assert result1[1] == result2[1]  # reward

    def test_fallback_for_unknown_action(self):
        env = AixiEnvironment(self._make_spec(), [0.5] * 72, seed=42)
        env.reset()
        obs, reward, done, info = env.step("reflect_on_self")
        # reflect_on_self has no transition_weights, fallback to random obs
        assert obs in {"user_happy", "user_curious", "silence"}

    def test_empty_spec_still_works(self):
        spec = EnvironmentSpec()
        env = AixiEnvironment(spec, [0.5] * 72, seed=42)
        obs = env.reset()
        assert obs == "initial_state"
        obs, reward, done, info = env.step("noop")
        assert obs == "obs_1"


# ---------------------------------------------------------------------------
# EnvironmentBuilder tests
# ---------------------------------------------------------------------------


class TestEnvironmentBuilderFromNeuralEngine:
    """Tests for building environment from NeuralEngine patterns."""

    def test_builds_spec_from_episodes(self):
        episodes = [
            {"content": "I love nature and flowers"},
            {"content": "Nature is beautiful and peaceful"},
            {"content": "The flowers bloom in spring"},
        ]
        neural = NeuralEngine(seed=42)
        personality = [0.5] * 72

        spec = EnvironmentBuilder.from_neural_engine(neural, episodes, personality)

        assert isinstance(spec, EnvironmentSpec)
        assert len(spec.actions) > 0
        assert len(spec.observations) > 0
        assert len(spec.reward_signals) > 0
        assert spec.horizon >= 3
        assert 0.0 < spec.gamma <= 1.0

    def test_includes_base_actions(self):
        episodes = [{"content": "Hello world"}]
        neural = NeuralEngine(seed=42)
        personality = [0.5] * 72

        spec = EnvironmentBuilder.from_neural_engine(neural, episodes, personality)

        assert "respond_empathically" in spec.actions
        assert "ask_question" in spec.actions
        assert "explore_topic" in spec.actions

    def test_includes_topic_derived_actions(self):
        episodes = [
            {"content": "Music is my passion and I love playing music"},
            {"content": "Playing guitar brings me happiness and music"},
        ]
        neural = NeuralEngine(seed=42)
        personality = [0.5] * 72

        spec = EnvironmentBuilder.from_neural_engine(neural, episodes, personality)

        # Should derive topic-specific actions from vocabulary
        action_text = " ".join(spec.actions)
        assert "music" in action_text.lower() or "playing" in action_text.lower()

    def test_includes_base_observations(self):
        episodes = [{"content": "Hello"}]
        neural = NeuralEngine(seed=42)
        personality = [0.5] * 72

        spec = EnvironmentBuilder.from_neural_engine(neural, episodes, personality)

        assert "user_engaged" in spec.observations
        assert "user_curious" in spec.observations
        assert "silence" in spec.observations

    def test_rewards_personality_modulated(self):
        episodes = [{"content": "Hello world"}]
        neural = NeuralEngine(seed=42)

        # High openness personality
        high_open = [0.5] * 72
        high_open[20] = 1.0

        low_open = [0.5] * 72
        low_open[20] = 0.0

        spec_high = EnvironmentBuilder.from_neural_engine(neural, episodes, high_open)
        spec_low = EnvironmentBuilder.from_neural_engine(neural, episodes, low_open)

        # "explore" reward should be higher for open personality
        assert spec_high.reward_signals.get("explore", 0) > spec_low.reward_signals.get("explore", 0)

    def test_horizon_scales_with_episodes(self):
        few_eps = [{"content": "Hello"}]
        many_eps = [{"content": f"Episode {i}"} for i in range(15)]
        neural = NeuralEngine(seed=42)
        personality = [0.5] * 72

        spec_few = EnvironmentBuilder.from_neural_engine(neural, few_eps, personality)
        spec_many = EnvironmentBuilder.from_neural_engine(neural, many_eps, personality)

        assert spec_many.horizon >= spec_few.horizon

    def test_transition_weights_populated(self):
        episodes = [{"content": "Test interaction"}]
        neural = NeuralEngine(seed=42)
        personality = [0.5] * 72

        spec = EnvironmentBuilder.from_neural_engine(neural, episodes, personality)

        # Each action should have transitions
        for action in spec.actions:
            assert action in spec.transition_weights
            assert len(spec.transition_weights[action]) > 0

    def test_empty_episodes(self):
        neural = NeuralEngine(seed=42)
        personality = [0.5] * 72

        spec = EnvironmentBuilder.from_neural_engine(neural, [], personality)

        assert isinstance(spec, EnvironmentSpec)
        assert len(spec.actions) >= 5  # base actions


class TestEnvironmentBuilderFromLLM:
    """Tests for building environment from LLM client."""

    def test_uses_llm_extract_method(self):
        mock_llm = type("MockLLM", (), {
            "extract_environment_spec": lambda self, eps, summary: {
                "actions": ["llm_action_1", "llm_action_2"],
                "observations": ["obs_1", "obs_2"],
                "reward_signals": {"llm_action_1": 0.5},
                "horizon": 12,
                "gamma": 0.9,
            }
        })()

        spec = EnvironmentBuilder.from_llm(
            mock_llm,
            [{"content": "test"}],
            "personality summary",
            [0.5] * 72,
        )

        assert "llm_action_1" in spec.actions
        assert "llm_action_2" in spec.actions
        assert "obs_1" in spec.observations
        assert spec.horizon == 12
        assert spec.gamma == 0.9

    def test_falls_back_when_no_extract_method(self):
        mock_llm = type("MockLLM", (), {})()

        spec = EnvironmentBuilder.from_llm(
            mock_llm,
            [{"content": "test"}],
            "personality summary",
            [0.5] * 72,
        )

        # Should fall back to NeuralEngine-based spec
        assert isinstance(spec, EnvironmentSpec)
        assert len(spec.actions) >= 5

    def test_falls_back_on_llm_error(self):
        mock_llm = type("MockLLM", (), {
            "extract_environment_spec": lambda self, eps, summary: (_ for _ in ()).throw(RuntimeError("API error"))
        })()

        spec = EnvironmentBuilder.from_llm(
            mock_llm,
            [{"content": "test"}],
            "personality summary",
            [0.5] * 72,
        )

        assert isinstance(spec, EnvironmentSpec)
        assert len(spec.actions) >= 5


class TestEnvironmentBuilderParseLLMSpec:
    """Tests for parsing LLM-returned environment specs."""

    def test_parses_valid_spec(self):
        raw = {
            "actions": ["act1", "act2"],
            "observations": ["obs1"],
            "reward_signals": {"act1": 0.5},
            "transition_weights": {
                "act1": [["obs1", 1.0]],
            },
            "horizon": 8,
            "gamma": 0.9,
        }
        spec = EnvironmentBuilder._parse_llm_spec(raw)
        assert spec.actions == ["act1", "act2"]
        assert spec.observations == ["obs1"]
        assert spec.reward_signals == {"act1": 0.5}
        assert spec.horizon == 8
        assert spec.gamma == 0.9

    def test_handles_empty_dict(self):
        spec = EnvironmentBuilder._parse_llm_spec({})
        assert spec.actions == []
        assert spec.observations == []
        assert spec.horizon == 10

    def test_handles_non_dict(self):
        spec = EnvironmentBuilder._parse_llm_spec("not a dict")
        assert spec.actions == []

    def test_clamps_horizon(self):
        spec = EnvironmentBuilder._parse_llm_spec({"horizon": 100})
        assert spec.horizon <= 50

    def test_clamps_gamma(self):
        spec = EnvironmentBuilder._parse_llm_spec({"gamma": 2.0})
        assert spec.gamma <= 1.0


# ---------------------------------------------------------------------------
# DreamEngine with AixiEnvironment tests
# ---------------------------------------------------------------------------


class TestDreamEngineWithEnvironment:
    """Tests for DreamEngine using AIXI environment rollouts."""

    def test_builds_environment_on_first_rollout(self):
        engine = DreamEngine(seed=42)
        history = [{"content": "hello world"}]
        personality = [0.5] * 72

        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=10, top_k=5
        )

        assert engine.environment_spec is not None
        assert len(engine.environment_spec.actions) > 0

    def test_hypotheses_contain_action_traces(self):
        engine = DreamEngine(seed=42)
        history = [
            {"content": "I love nature"},
            {"content": "Nature makes me happy"},
        ]
        personality = [0.5] * 72

        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=50, top_k=5
        )

        for h in results:
            # Hypothesis actions should contain arrow-separated traces
            assert isinstance(h.action, str)
            assert len(h.action) > 0

    def test_environment_reused_across_calls(self):
        engine = DreamEngine(seed=42)
        history = [{"content": "test"}]
        personality = [0.5] * 72

        engine.perform_dream_rollouts(history, personality, num_rollouts=10, top_k=3)
        spec1 = engine.environment_spec

        # Second call should reuse the same spec
        engine.perform_dream_rollouts(history, personality, num_rollouts=10, top_k=3)
        spec2 = engine.environment_spec

        assert spec1 is spec2

    def test_llm_client_used_for_environment(self):
        mock_llm = type("MockLLM", (), {
            "extract_environment_spec": lambda self, eps, summary: {
                "actions": ["llm_explore", "llm_reflect"],
                "observations": ["llm_obs_1"],
                "reward_signals": {"llm_explore": 0.8},
                "horizon": 8,
                "gamma": 0.9,
            }
        })()

        engine = DreamEngine(seed=42, llm_client=mock_llm)
        history = [{"content": "test"}]
        personality = [0.5] * 72

        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=20, top_k=5
        )

        spec = engine.environment_spec
        assert spec is not None
        assert "llm_explore" in spec.actions
        assert spec.horizon == 8

    def test_explicit_build_then_rollouts(self):
        engine = DreamEngine(seed=42)
        history = [{"content": "test episode"}]
        personality = [0.5] * 72

        # Explicitly build environment first
        spec = engine.build_environment(history, personality, "summary")
        assert len(spec.actions) > 0

        # Then run rollouts (should use pre-built environment)
        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=10, top_k=5
        )
        assert len(results) == 5
        assert engine.environment_spec is spec


# ---------------------------------------------------------------------------
# SleepCycle with environment integration tests
# ---------------------------------------------------------------------------


class TestSleepCycleEnvironment:
    """Tests for SleepCycle with AIXI environment integration."""

    def _make_state(self) -> PersonalityState:
        return PersonalityState(being_id="env-test", name="Tester")

    def test_run_includes_environment_spec(self):
        state = self._make_state()
        episodes = [
            {"content": "Hello world"},
            {"content": "Nature is beautiful"},
        ]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))
        new_state, result = cycle.run(state, episodes, num_rollouts=10, svd_rank=4)

        assert result.environment_spec is not None
        assert len(result.environment_spec.actions) > 0
        assert len(result.environment_spec.observations) > 0

    def test_continuous_includes_environment_spec(self):
        state = self._make_state()
        episodes = [{"content": "Test episode"}]
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        def stop_after_1(cycle_num, _state):
            if cycle_num >= 1:
                cycle.request_stop()

        _, result = cycle.run_continuous(
            state, episodes, num_rollouts=10, svd_rank=4, on_cycle=stop_after_1
        )

        assert result.environment_spec is not None

    def test_run_with_llm_builds_environment_from_llm(self):
        mock_llm = type("MockLLM", (), {
            "extract_environment_spec": lambda self, eps, summary: {
                "actions": ["llm_act_1", "llm_act_2"],
                "observations": ["llm_obs_1"],
                "reward_signals": {"llm_act_1": 0.6},
                "horizon": 7,
                "gamma": 0.88,
            }
        })()

        state = self._make_state()
        episodes = [{"content": "Test with LLM"}]
        dream_engine = DreamEngine(seed=42, llm_client=mock_llm)
        cycle = SleepCycle(dream_engine=dream_engine)

        _, result = cycle.run(state, episodes, num_rollouts=10, svd_rank=4)

        spec = result.environment_spec
        assert spec is not None
        assert "llm_act_1" in spec.actions
        assert spec.horizon == 7
        assert spec.gamma == 0.88
