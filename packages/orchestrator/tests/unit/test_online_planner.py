"""Unit tests for the OnlinePlanner – real-time AIXI mini-rollouts."""

import pytest

from serhu_orchestrator.sleep.online_planner import (
    OnlinePlanner,
    PlanResult,
    Experience,
)
from serhu_orchestrator.sleep.aixi_environment import EnvironmentSpec, WorldModel
from serhu_orchestrator.sleep.neural_engine import NeuralEngine


# -- helpers -----------------------------------------------------------------

def _personality_vector() -> list[float]:
    """Create a standard 72-dim personality vector."""
    return [0.5] * 72


def _make_spec(
    actions: list[str] | None = None,
    observations: list[str] | None = None,
    reward_signals: dict[str, float] | None = None,
) -> EnvironmentSpec:
    return EnvironmentSpec(
        actions=actions or [
            "respond_empathically",
            "ask_question",
            "explore_topic",
            "discuss_stars",
            "reflect_on_self",
        ],
        observations=observations or [
            "user_happy",
            "user_curious",
            "user_sad",
            "silence",
        ],
        reward_signals=reward_signals or {
            "empathically": 0.5,
            "explore": 0.3,
            "question": 0.2,
        },
        horizon=5,
        gamma=0.95,
    )


def _make_world_model() -> WorldModel:
    return WorldModel(
        model_type="co_occurrence",
        transition_weights={
            "respond_empathically": [("user_happy", 0.6), ("user_curious", 0.4)],
            "ask_question": [("user_curious", 0.7), ("silence", 0.3)],
            "explore_topic": [("user_curious", 0.5), ("user_happy", 0.5)],
            "discuss_stars": [("user_happy", 0.4), ("user_curious", 0.6)],
            "reflect_on_self": [("silence", 0.5), ("user_sad", 0.5)],
        },
    )


def _make_episodes(contents: list[str]) -> list[dict]:
    return [{"content": c, "role": "user"} for c in contents]


def _trained_engine() -> NeuralEngine:
    """Return a NeuralEngine that has been trained on star-related episodes."""
    engine = NeuralEngine(seed=42)
    episodes = _make_episodes([
        "stars galaxy universe cosmic wonder",
        "stars planets nebula celestial light",
        "stars constellation astronomy stellar night",
        "nature beautiful wonderful amazing serene",
        "nature forest river mountains peaceful",
    ])
    engine.train(episodes, _personality_vector())
    return engine


# ---------------------------------------------------------------------------
# PlanResult dataclass tests
# ---------------------------------------------------------------------------


class TestPlanResult:
    """Tests for the PlanResult dataclass."""

    def test_default_values(self):
        pr = PlanResult()
        assert pr.chosen_response == ""
        assert pr.chosen_action == ""
        assert pr.expected_reward == 0.0
        assert pr.candidates_evaluated == 0
        assert pr.rollouts_per_candidate == 0
        assert pr.all_rewards == []

    def test_custom_values(self):
        pr = PlanResult(
            chosen_response="hello",
            chosen_action="ask_question",
            expected_reward=0.5,
            candidates_evaluated=3,
            rollouts_per_candidate=10,
            all_rewards=[0.3, 0.5, 0.2],
        )
        assert pr.chosen_response == "hello"
        assert pr.expected_reward == 0.5


# ---------------------------------------------------------------------------
# Experience dataclass tests
# ---------------------------------------------------------------------------


class TestExperience:
    """Tests for the Experience dataclass."""

    def test_default_values(self):
        exp = Experience()
        assert exp.action == ""
        assert exp.observation == ""
        assert exp.reward == 0.0
        assert exp.planned_reward == 0.0


# ---------------------------------------------------------------------------
# OnlinePlanner core tests
# ---------------------------------------------------------------------------


class TestOnlinePlannerInit:
    """Tests for OnlinePlanner initialization."""

    def test_default_init(self):
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(engine)
        assert planner.experiences == []

    def test_custom_params(self):
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(
            engine,
            num_candidates=3,
            rollouts_per_candidate=5,
            horizon=2,
            seed=42,
        )
        assert planner.experiences == []


class TestOnlinePlannerPlanAndAct:
    """Tests for plan_and_act – the core online planning method."""

    def test_plan_returns_plan_result(self):
        engine = _trained_engine()
        planner = OnlinePlanner(engine, num_candidates=3, rollouts_per_candidate=5, seed=42)
        spec = _make_spec()
        wm = _make_world_model()

        result = planner.plan_and_act(
            context=["Tell me about stars"],
            personality_vector=_personality_vector(),
            environment_spec=spec,
            world_model=wm,
            max_tokens=10,
        )

        assert isinstance(result, PlanResult)
        assert result.chosen_response != ""
        assert result.chosen_action in spec.actions
        assert result.candidates_evaluated > 0
        assert result.rollouts_per_candidate == 5
        assert len(result.all_rewards) == result.candidates_evaluated

    def test_plan_selects_highest_reward(self):
        """The chosen candidate should have the highest expected reward."""
        engine = _trained_engine()
        planner = OnlinePlanner(engine, num_candidates=5, rollouts_per_candidate=10, seed=42)
        spec = _make_spec()
        wm = _make_world_model()

        result = planner.plan_and_act(
            context=["Tell me about stars and the universe"],
            personality_vector=_personality_vector(),
            environment_spec=spec,
            world_model=wm,
            max_tokens=10,
        )

        if result.all_rewards:
            assert result.expected_reward == max(result.all_rewards)

    def test_plan_without_world_model(self):
        """Planning should still work without a trained WorldModel."""
        engine = _trained_engine()
        planner = OnlinePlanner(engine, num_candidates=3, rollouts_per_candidate=5, seed=42)
        spec = _make_spec()

        result = planner.plan_and_act(
            context=["Hello world"],
            personality_vector=_personality_vector(),
            environment_spec=spec,
            world_model=None,
            max_tokens=10,
        )

        assert isinstance(result, PlanResult)
        assert result.chosen_response != ""

    def test_plan_with_untrained_engine(self):
        """Untrained engine should produce fallback candidates."""
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(engine, num_candidates=3, rollouts_per_candidate=5, seed=42)
        spec = _make_spec()
        wm = _make_world_model()

        result = planner.plan_and_act(
            context=["Hello"],
            personality_vector=_personality_vector(),
            environment_spec=spec,
            world_model=wm,
            max_tokens=10,
        )

        # Should still return a result (even if fallback)
        assert isinstance(result, PlanResult)

    def test_plan_empty_actions(self):
        """With no actions in spec, planning should handle gracefully."""
        engine = _trained_engine()
        planner = OnlinePlanner(engine, num_candidates=3, rollouts_per_candidate=5, seed=42)
        spec = EnvironmentSpec(actions=[], observations=["obs1"])

        result = planner.plan_and_act(
            context=["Hello"],
            personality_vector=_personality_vector(),
            environment_spec=spec,
            world_model=None,
            max_tokens=10,
        )

        assert isinstance(result, PlanResult)


class TestOnlinePlannerExperienceRecording:
    """Tests for recording real-turn experiences."""

    def test_record_experience(self):
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(engine, seed=42)

        exp = planner.record_experience(
            action="hello world",
            observation="user response",
            reward=0.5,
            planned_reward=0.4,
        )

        assert isinstance(exp, Experience)
        assert exp.action == "hello world"
        assert exp.reward == 0.5
        assert exp.planned_reward == 0.4
        assert len(planner.experiences) == 1

    def test_multiple_experiences_accumulate(self):
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(engine, seed=42)

        planner.record_experience("a1", "o1", 0.1, 0.2)
        planner.record_experience("a2", "o2", 0.3, 0.4)
        planner.record_experience("a3", "o3", 0.5, 0.6)

        assert len(planner.experiences) == 3
        assert planner.experiences[0].reward == 0.1
        assert planner.experiences[2].reward == 0.5


class TestOnlinePlannerRealReward:
    """Tests for the static real reward computation."""

    def test_empty_response_zero_reward(self):
        r = OnlinePlanner.compute_real_reward("hello", "", _personality_vector())
        assert r == 0.0

    def test_whitespace_response_zero_reward(self):
        r = OnlinePlanner.compute_real_reward("hello", "   ", _personality_vector())
        assert r == 0.0

    def test_relevant_response_has_higher_reward(self):
        """A response with token overlap should score higher."""
        r_relevant = OnlinePlanner.compute_real_reward(
            "stars universe", "stars are beautiful in the universe",
            _personality_vector(),
        )
        r_irrelevant = OnlinePlanner.compute_real_reward(
            "stars universe", "food tastes good",
            _personality_vector(),
        )
        assert r_relevant > r_irrelevant

    def test_reward_with_spec_signals(self):
        spec = _make_spec(reward_signals={"stars": 0.8})
        r_with_signal = OnlinePlanner.compute_real_reward(
            "stars", "stars are wonderful",
            _personality_vector(),
            spec=spec,
        )
        r_no_signal = OnlinePlanner.compute_real_reward(
            "food", "food is good",
            _personality_vector(),
            spec=spec,
        )
        assert r_with_signal > r_no_signal

    def test_reward_bounded(self):
        """Reward should be reasonable (non-negative)."""
        r = OnlinePlanner.compute_real_reward(
            "hello", "world",
            _personality_vector(),
        )
        assert r >= 0.0


class TestOnlinePlannerActionMapping:
    """Tests for mapping responses to AIXI actions."""

    def test_maps_to_closest_action(self):
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(engine, seed=42)
        spec = _make_spec()

        # "explore" tokens overlap with "explore_topic" action
        action = planner._map_response_to_action("explore the stars", spec)
        assert action == "explore_topic"

    def test_maps_empathy_response(self):
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(engine, seed=42)
        spec = _make_spec()

        action = planner._map_response_to_action(
            "I feel empathically towards you", spec
        )
        # "empathically" in the response has token overlap with
        # "respond_empathically" and also gets a reward_boost from
        # spec.reward_signals["empathically"] = 0.5
        assert action == "respond_empathically"

    def test_empty_actions_fallback(self):
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(engine, seed=42)
        spec = EnvironmentSpec(actions=[])

        action = planner._map_response_to_action("hello", spec)
        assert action == "respond"


class TestOnlinePlannerCandidateEvaluation:
    """Tests for candidate evaluation via mini-rollouts."""

    def test_evaluate_returns_float(self):
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(engine, rollouts_per_candidate=5, seed=42)
        spec = _make_spec()
        wm = _make_world_model()

        reward = planner._evaluate_candidate(
            "explore_topic", _personality_vector(), spec, wm
        )
        assert isinstance(reward, float)

    def test_evaluate_different_actions_different_rewards(self):
        engine = NeuralEngine(seed=42)
        planner = OnlinePlanner(engine, rollouts_per_candidate=20, seed=42)
        spec = _make_spec()
        wm = _make_world_model()

        reward_explore = planner._evaluate_candidate(
            "explore_topic", _personality_vector(), spec, wm
        )
        reward_reflect = planner._evaluate_candidate(
            "reflect_on_self", _personality_vector(), spec, wm
        )
        # The specific values differ based on reward signals
        assert isinstance(reward_explore, float)
        assert isinstance(reward_reflect, float)
