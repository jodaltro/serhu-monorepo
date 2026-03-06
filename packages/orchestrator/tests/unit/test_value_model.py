"""Unit tests for the ValueModel – lightweight reward predictor."""

import pytest

from serhu_orchestrator.sleep.value_model import ValueModel


# -- helpers -----------------------------------------------------------------

def _personality_vector() -> list[float]:
    """Create a standard 72-dim personality vector."""
    return [0.5] * 72


# ---------------------------------------------------------------------------
# ValueModel dataclass tests
# ---------------------------------------------------------------------------


class TestValueModelInit:
    """Tests for ValueModel initialization and defaults."""

    def test_default_values(self):
        vm = ValueModel()
        assert vm.weights == {}
        assert vm.bias == 0.0
        assert vm.version == ""
        assert vm.metrics == {}
        assert vm.learning_rate == 0.01

    def test_custom_learning_rate(self):
        vm = ValueModel(learning_rate=0.05)
        assert vm.learning_rate == 0.05

    def test_is_trained_false_initially(self):
        vm = ValueModel()
        assert vm.is_trained is False


# ---------------------------------------------------------------------------
# ValueModel.fit tests
# ---------------------------------------------------------------------------


class TestValueModelFit:
    """Tests for ValueModel training."""

    def test_fit_returns_metrics(self):
        vm = ValueModel()
        pairs = [
            ([0.5] * 72, "explore_topic"),
            ([0.5] * 72, "ask_question"),
            ([0.5] * 72, "reflect_on_self"),
        ]
        targets = [0.8, 0.5, 0.3]

        metrics = vm.fit(pairs, targets)

        assert "mse" in metrics
        assert "samples" in metrics
        assert "r_squared" in metrics
        assert metrics["samples"] == 3.0

    def test_fit_sets_is_trained(self):
        vm = ValueModel()
        pairs = [([0.5] * 72, "explore_topic")]
        targets = [0.5]

        vm.fit(pairs, targets)
        assert vm.is_trained is True

    def test_fit_sets_version(self):
        vm = ValueModel()
        pairs = [([0.5] * 72, "explore_topic")]
        targets = [0.5]

        vm.fit(pairs, targets)
        assert vm.version != ""
        assert len(vm.version) == 12  # sha256[:12]

    def test_fit_empty_pairs(self):
        vm = ValueModel()
        metrics = vm.fit([], [])
        assert metrics["samples"] == 0
        assert vm.is_trained is False

    def test_fit_mismatched_lengths(self):
        vm = ValueModel()
        pairs = [([0.5] * 72, "explore")]
        targets = [0.5, 0.3]  # Different length
        metrics = vm.fit(pairs, targets)
        assert metrics["samples"] == 0

    def test_fit_reduces_mse_over_epochs(self):
        vm = ValueModel(learning_rate=0.1)
        pairs = [
            ([0.5] * 72, "explore_topic"),
            ([0.5] * 72, "ask_question"),
        ]
        targets = [0.8, 0.2]

        # Train with 1 epoch
        vm1 = ValueModel(learning_rate=0.1)
        m1 = vm1.fit(pairs, targets, epochs=1)

        # Train with many epochs
        vm2 = ValueModel(learning_rate=0.1)
        m2 = vm2.fit(pairs, targets, epochs=50)

        assert m2["mse"] <= m1["mse"]

    def test_fit_different_data_different_versions(self):
        vm1 = ValueModel()
        vm1.fit([([0.5] * 72, "explore")], [0.8])

        vm2 = ValueModel()
        vm2.fit([([0.5] * 72, "reflect")], [0.2])

        assert vm1.version != vm2.version


# ---------------------------------------------------------------------------
# ValueModel.predict tests
# ---------------------------------------------------------------------------


class TestValueModelPredict:
    """Tests for ValueModel prediction."""

    def test_predict_returns_float(self):
        vm = ValueModel()
        vm.fit(
            [([0.5] * 72, "explore_topic")],
            [0.5],
        )
        pred = vm.predict([0.5] * 72, "explore_topic")
        assert isinstance(pred, float)

    def test_untrained_predicts_zero(self):
        vm = ValueModel()
        pred = vm.predict([0.5] * 72, "explore_topic")
        assert pred == 0.0

    def test_trained_model_differentiates_actions(self):
        vm = ValueModel(learning_rate=0.1)
        pairs = [
            ([0.5] * 72, "explore_topic"),
            ([0.5] * 72, "explore_topic"),
            ([0.5] * 72, "reflect_on_self"),
            ([0.5] * 72, "reflect_on_self"),
        ]
        targets = [0.9, 0.8, 0.1, 0.2]

        vm.fit(pairs, targets, epochs=50)

        pred_explore = vm.predict([0.5] * 72, "explore_topic")
        pred_reflect = vm.predict([0.5] * 72, "reflect_on_self")

        # Model should learn that explore has higher reward
        assert pred_explore > pred_reflect


# ---------------------------------------------------------------------------
# ValueModel.rank tests
# ---------------------------------------------------------------------------


class TestValueModelRank:
    """Tests for ValueModel ranking."""

    def test_rank_returns_top_k(self):
        vm = ValueModel(learning_rate=0.1)
        pairs = [
            ([0.5] * 72, "action_a"),
            ([0.5] * 72, "action_b"),
            ([0.5] * 72, "action_c"),
            ([0.5] * 72, "action_d"),
            ([0.5] * 72, "action_e"),
        ]
        targets = [0.9, 0.7, 0.5, 0.3, 0.1]
        vm.fit(pairs, targets, epochs=50)

        ranked = vm.rank([0.5] * 72, ["action_a", "action_b", "action_c", "action_d", "action_e"], top_k=3)

        assert len(ranked) == 3
        for idx, action, score in ranked:
            assert isinstance(idx, int)
            assert isinstance(action, str)
            assert isinstance(score, float)

    def test_rank_sorted_descending(self):
        vm = ValueModel(learning_rate=0.1)
        pairs = [
            ([0.5] * 72, "high_reward_action"),
            ([0.5] * 72, "low_reward_action"),
        ]
        targets = [0.9, 0.1]
        vm.fit(pairs, targets, epochs=50)

        ranked = vm.rank([0.5] * 72, ["high_reward_action", "low_reward_action"], top_k=2)

        assert ranked[0][2] >= ranked[1][2]

    def test_rank_preserves_original_indices(self):
        vm = ValueModel(learning_rate=0.1)
        pairs = [
            ([0.5] * 72, "action_low"),
            ([0.5] * 72, "action_high"),
        ]
        targets = [0.1, 0.9]
        vm.fit(pairs, targets, epochs=50)

        ranked = vm.rank([0.5] * 72, ["action_low", "action_high"], top_k=2)

        # The highest ranked should be index 1 (action_high)
        assert ranked[0][0] == 1
        assert ranked[0][1] == "action_high"

    def test_rank_top_k_larger_than_actions(self):
        vm = ValueModel()
        vm.fit([([0.5] * 72, "a")], [0.5])

        ranked = vm.rank([0.5] * 72, ["a", "b"], top_k=10)
        assert len(ranked) == 2


# ---------------------------------------------------------------------------
# ValueModel._featurize tests
# ---------------------------------------------------------------------------


class TestValueModelFeaturize:
    """Tests for feature extraction."""

    def test_featurize_includes_action_tokens(self):
        features = ValueModel._featurize([0.5] * 72, "explore_topic")
        assert "act:explore" in features
        assert "act:topic" in features

    def test_featurize_includes_personality_summary(self):
        features = ValueModel._featurize([0.5] * 72, "test")
        assert "pv_mean" in features
        assert "pv_std" in features
        assert features["pv_mean"] == pytest.approx(0.5)

    def test_featurize_includes_action_length(self):
        features = ValueModel._featurize([0.5] * 72, "test")
        assert "act_len" in features
        assert 0.0 <= features["act_len"] <= 1.0

    def test_featurize_empty_state(self):
        features = ValueModel._featurize([], "test")
        assert features["pv_mean"] == 0.0
        assert features["pv_std"] == 0.0

    def test_featurize_empty_action(self):
        features = ValueModel._featurize([0.5] * 72, "")
        assert "pv_mean" in features
        assert features["act_len"] == 0.0


# ---------------------------------------------------------------------------
# ValueModel versioning tests
# ---------------------------------------------------------------------------


class TestValueModelVersioning:
    """Tests for content-based versioning."""

    def test_version_is_deterministic(self):
        vm1 = ValueModel()
        vm1.fit([([0.5] * 72, "a")], [0.5])

        vm2 = ValueModel()
        vm2.fit([([0.5] * 72, "a")], [0.5])

        assert vm1.version == vm2.version

    def test_version_changes_after_refit(self):
        vm = ValueModel()
        vm.fit([([0.5] * 72, "a")], [0.5])
        v1 = vm.version

        vm.fit([([0.5] * 72, "b")], [0.9])
        v2 = vm.version

        assert v1 != v2
