"""Tests for the NeuralEngine – transformer-inspired self-learning.

Validates the core self-learning mechanisms:
- TF-IDF vocabulary construction
- Self-attention pattern discovery
- N-gram pattern mining
- Personality-weighted coherence scoring
- Response generation from learned patterns
- Semantic fact extraction
- Belief derivation
"""

import pytest

from serhu_orchestrator.sleep.neural_engine import (
    NeuralEngine,
    LearnedPattern,
    TrainingResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_episodes(contents: list[str]) -> list[dict]:
    """Create episode dicts from content strings."""
    return [{"content": c, "role": "user"} for c in contents]


def _personality_vector() -> list[float]:
    """Standard 72-dim personality vector (HEXACO+TCI+Schwartz)."""
    return [0.5] * 72


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


class TestNeuralEngineTraining:
    """Tests for the training phase."""

    def test_train_returns_training_result(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes(["hello world", "hello again"])
        result = engine.train(episodes, _personality_vector())
        assert isinstance(result, TrainingResult)
        assert result.vocabulary_size > 0
        assert result.pattern_count > 0

    def test_train_sets_trained_flag(self):
        engine = NeuralEngine(seed=42)
        assert engine.is_trained is False
        engine.train(_make_episodes(["test"]), _personality_vector())
        assert engine.is_trained is True

    def test_train_empty_episodes(self):
        engine = NeuralEngine(seed=42)
        result = engine.train([], _personality_vector())
        assert result.vocabulary_size == 0
        assert result.pattern_count == 0

    def test_vocabulary_built_from_content(self):
        engine = NeuralEngine(seed=42)
        engine.train(
            _make_episodes(["stars planets galaxy", "stars nebula galaxy"]),
            _personality_vector(),
        )
        assert "stars" in engine._vocabulary
        assert "galaxy" in engine._vocabulary
        assert engine._vocabulary["stars"] > 0

    def test_stop_words_excluded_from_vocabulary(self):
        engine = NeuralEngine(seed=42)
        engine.train(
            _make_episodes(["the sun is bright and the moon is dim"]),
            _personality_vector(),
        )
        # Stop words should not be in the vocabulary
        assert "the" not in engine._vocabulary
        assert "and" not in engine._vocabulary
        # Content words should be present
        assert "bright" in engine._vocabulary or "moon" in engine._vocabulary

    def test_bigrams_extracted(self):
        engine = NeuralEngine(seed=42)
        engine.train(
            _make_episodes([
                "stars are beautiful",
                "stars are wonderful",
            ]),
            _personality_vector(),
        )
        assert len(engine._bigrams) > 0

    def test_attention_matrix_computed(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes(["topic alpha", "topic beta", "topic alpha"])
        engine.train(episodes, _personality_vector())
        assert len(engine._attention_matrix) == 3
        assert len(engine._attention_matrix[0]) == 3
        # Attention weights should sum to ~1.0 per row (softmax)
        for row in engine._attention_matrix:
            assert abs(sum(row) - 1.0) < 0.01

    def test_training_result_has_top_patterns(self):
        engine = NeuralEngine(seed=42)
        result = engine.train(
            _make_episodes([
                "nature beautiful peaceful",
                "nature wonderful peaceful",
                "nature serene calm",
            ]),
            _personality_vector(),
        )
        assert len(result.top_patterns) > 0
        assert any("nature" in p for p in result.top_patterns)

    def test_training_result_attention_entropy(self):
        engine = NeuralEngine(seed=42)
        result = engine.train(
            _make_episodes(["hello world"] * 5),
            _personality_vector(),
        )
        assert result.attention_entropy >= 0.0

    def test_personality_influences_pattern_scoring(self):
        """High openness should boost novel patterns."""
        engine = NeuralEngine(seed=42)
        high_openness = [0.5] * 20 + [0.9] * 4 + [0.5] * 48  # openness at index 20-23
        engine.train(
            _make_episodes(["novel idea creative thought", "standard routine work"]),
            high_openness,
        )
        # Should complete without error and have patterns
        assert engine.pattern_count > 0


# ---------------------------------------------------------------------------
# Hypothesis Generation
# ---------------------------------------------------------------------------


class TestNeuralEngineHypotheses:
    """Tests for hypothesis generation."""

    def test_generate_hypotheses_returns_list(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes(["stars planets galaxy", "stars nebula"])
        hyps = engine.generate_hypotheses(episodes, _personality_vector(), num_hypotheses=5)
        assert isinstance(hyps, list)
        assert len(hyps) <= 5

    def test_hypotheses_from_learned_patterns(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes([
            "honesty truth integrity",
            "honesty respect values",
            "honesty kindness compassion",
        ])
        engine.train(episodes, _personality_vector())
        hyps = engine.generate_hypotheses(episodes, _personality_vector(), num_hypotheses=10)
        assert len(hyps) > 0
        assert any("honesty" in h.lower() for h in hyps)

    def test_hypotheses_empty_episodes(self):
        engine = NeuralEngine(seed=42)
        hyps = engine.generate_hypotheses([], _personality_vector(), num_hypotheses=5)
        # Should return empty list without crashing
        assert isinstance(hyps, list)

    def test_auto_trains_if_not_trained(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes(["learning happens automatically"])
        hyps = engine.generate_hypotheses(episodes, _personality_vector(), num_hypotheses=3)
        assert engine.is_trained
        assert isinstance(hyps, list)


# ---------------------------------------------------------------------------
# Semantic Fact Extraction
# ---------------------------------------------------------------------------


class TestNeuralEngineFacts:
    """Tests for semantic fact extraction."""

    def test_extract_facts_from_episodes(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes([
            "nature beautiful serene",
            "nature wonderful peaceful",
            "nature calming harmonious",
        ])
        engine.train(episodes, _personality_vector())
        facts = engine.extract_semantic_facts(episodes, _personality_vector())
        assert len(facts) > 0
        assert any("nature" in f.lower() for f in facts)

    def test_facts_include_frequent_tokens(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes([
            "python programming coding",
            "python language beautiful",
            "python development software",
        ])
        engine.train(episodes, _personality_vector())
        facts = engine.extract_semantic_facts(episodes, _personality_vector())
        assert any("python" in f.lower() for f in facts)

    def test_facts_limited_to_ten(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes([f"word{i} topic{i} subject{i}" for i in range(20)])
        engine.train(episodes, _personality_vector())
        facts = engine.extract_semantic_facts(episodes, _personality_vector())
        assert len(facts) <= 10

    def test_empty_episodes_return_no_facts(self):
        engine = NeuralEngine(seed=42)
        engine.train([], _personality_vector())
        facts = engine.extract_semantic_facts([], _personality_vector())
        assert len(facts) == 0


# ---------------------------------------------------------------------------
# Belief Derivation
# ---------------------------------------------------------------------------


class TestNeuralEngineBeliefs:
    """Tests for belief derivation."""

    def test_derive_beliefs_from_hypotheses(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes([
            "honesty truth important",
            "honesty respect values",
        ])
        engine.train(episodes, _personality_vector())

        beliefs = engine.derive_beliefs(
            ["hypothesis_about:honesty truth", "hypothesis_about:respect"],
            _personality_vector(),
        )
        assert len(beliefs) > 0
        assert all("Learned:" in b for b in beliefs)

    def test_derive_beliefs_empty_hypotheses(self):
        engine = NeuralEngine(seed=42)
        beliefs = engine.derive_beliefs([], _personality_vector())
        assert len(beliefs) == 0

    def test_beliefs_limited_to_three(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes(["word" * 50])
        engine.train(episodes, _personality_vector())
        beliefs = engine.derive_beliefs(
            [f"hypothesis_{i}" for i in range(20)],
            _personality_vector(),
        )
        assert len(beliefs) <= 3


# ---------------------------------------------------------------------------
# Response Generation
# ---------------------------------------------------------------------------


class TestNeuralEngineResponse:
    """Tests for self-generated responses."""

    def test_untrained_returns_fallback(self):
        engine = NeuralEngine(seed=42)
        response = engine.generate_response(["Hello"], _personality_vector())
        assert isinstance(response, str)
        assert len(response) > 0

    def test_trained_generates_from_patterns(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes([
            "stars galaxy universe cosmic",
            "stars planets nebula celestial",
            "stars constellation astronomy stellar",
        ])
        engine.train(episodes, _personality_vector())
        response = engine.generate_response(
            ["Tell me about stars"],
            _personality_vector(),
            max_tokens=10,
        )
        assert isinstance(response, str)
        assert len(response) > 0
        # Response should contain learned vocabulary
        assert any(
            word in response.lower()
            for word in ["stars", "galaxy", "universe", "cosmic", "planets"]
        )

    def test_max_tokens_respected(self):
        engine = NeuralEngine(seed=42)
        episodes = _make_episodes([
            "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        ] * 3)
        engine.train(episodes, _personality_vector())
        response = engine.generate_response(
            ["something"],
            _personality_vector(),
            max_tokens=3,
        )
        # Response should not exceed max_tokens
        assert len(response.split()) <= 3

    def test_empty_context_returns_something(self):
        engine = NeuralEngine(seed=42)
        response = engine.generate_response([], _personality_vector())
        assert isinstance(response, str)


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------


class TestNeuralEngineTokenization:
    """Tests for the tokenization logic."""

    def test_tokenize_basic(self):
        tokens = NeuralEngine._tokenize_text("Hello world, this is great!")
        assert "hello" in tokens
        assert "world" in tokens
        assert "great" in tokens
        # "this" and "is" are stop words
        assert "this" not in tokens
        assert "is" not in tokens

    def test_tokenize_portuguese(self):
        tokens = NeuralEngine._tokenize_text("A natureza é linda e maravilhosa")
        assert "natureza" in tokens
        assert "linda" in tokens
        assert "maravilhosa" in tokens
        # Stop words excluded
        assert "é" not in tokens

    def test_tokenize_short_tokens_excluded(self):
        tokens = NeuralEngine._tokenize_text("I am a ok go it do")
        # Single-char tokens should be excluded
        assert all(len(t) >= 2 for t in tokens)

    def test_tokenize_empty_string(self):
        tokens = NeuralEngine._tokenize_text("")
        assert tokens == []


# ---------------------------------------------------------------------------
# Integration: Training → Hypothesis → Belief Pipeline
# ---------------------------------------------------------------------------


class TestNeuralEnginePipeline:
    """End-to-end pipeline tests."""

    def test_full_learning_pipeline(self):
        """Train → generate hypotheses → derive beliefs → generate response."""
        engine = NeuralEngine(seed=42)
        personality = _personality_vector()

        # Step 1: Train on episodic data
        episodes = _make_episodes([
            "nature is beautiful and peaceful",
            "the mountains bring serenity",
            "ocean waves calm the mind",
            "nature heals the spirit",
            "forests are magical places",
        ])
        result = engine.train(episodes, personality)
        assert result.vocabulary_size > 0
        assert result.pattern_count > 0

        # Step 2: Generate hypotheses
        hyps = engine.generate_hypotheses(episodes, personality, num_hypotheses=5)
        assert len(hyps) > 0

        # Step 3: Derive beliefs
        beliefs = engine.derive_beliefs(hyps, personality)
        assert len(beliefs) > 0

        # Step 4: Generate response
        response = engine.generate_response(
            ["Tell me about nature"],
            personality,
            max_tokens=20,
        )
        assert isinstance(response, str)
        assert len(response) > 0

    def test_learning_improves_with_more_data(self):
        """More episodes should yield more vocabulary and patterns."""
        engine_small = NeuralEngine(seed=42)
        engine_large = NeuralEngine(seed=42)
        personality = _personality_vector()

        small_episodes = _make_episodes(["stars galaxy"])
        large_episodes = _make_episodes([
            "stars galaxy universe cosmic energy",
            "planets orbit celestial bodies rotation",
            "nebula constellation astronomy stellar",
            "dark matter gravity quantum physics",
            "supernova black hole singularity event",
        ])

        result_small = engine_small.train(small_episodes, personality)
        result_large = engine_large.train(large_episodes, personality)

        assert result_large.vocabulary_size > result_small.vocabulary_size
        assert result_large.pattern_count > result_small.pattern_count

    def test_deterministic_with_seed(self):
        """Same seed + same data = same results."""
        personality = _personality_vector()
        episodes = _make_episodes([
            "consistent data leads to consistent learning",
            "determinism is important for testing",
        ])

        engine1 = NeuralEngine(seed=99)
        engine2 = NeuralEngine(seed=99)

        result1 = engine1.train(episodes, personality)
        result2 = engine2.train(episodes, personality)

        assert result1.vocabulary_size == result2.vocabulary_size
        assert result1.pattern_count == result2.pattern_count

        hyps1 = engine1.generate_hypotheses(episodes, personality, num_hypotheses=5)
        hyps2 = engine2.generate_hypotheses(episodes, personality, num_hypotheses=5)
        assert hyps1 == hyps2
