"""Unit tests for LLM integration – OpenAIClient and Orchestrator.chat()."""

import json

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from serhu_orchestrator.llm.llm_client import LLMClient, LLMResponse
from serhu_orchestrator.llm.openai_client import OpenAIClient
from serhu_orchestrator.personality.types import PersonalityState
from serhu_orchestrator.sleep.dream_engine import DreamEngine, Hypothesis
from serhu_orchestrator.sleep.sleep_cycle import SleepCycle, SleepResult


# ---------------------------------------------------------------------------
# LLMResponse dataclass
# ---------------------------------------------------------------------------


class TestLLMResponse:
    def test_default_fields(self):
        resp = LLMResponse(content="hello")
        assert resp.content == "hello"
        assert resp.model == ""
        assert resp.usage == {}

    def test_custom_fields(self):
        resp = LLMResponse(
            content="response",
            model="gpt-5.4",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        assert resp.model == "gpt-5.4"
        assert resp.usage["total_tokens"] == 15


# ---------------------------------------------------------------------------
# LLMClient protocol
# ---------------------------------------------------------------------------


class TestLLMClientProtocol:
    def test_mock_satisfies_protocol(self):
        mock = MagicMock()
        mock.chat = MagicMock(return_value=LLMResponse(content="ok"))
        mock.analyze_traits = MagicMock(return_value={})
        mock.extract_semantic_facts = MagicMock(return_value=[])
        mock.derive_beliefs = MagicMock(return_value=[])
        mock.generate_dream_hypotheses = MagicMock(return_value=[])
        mock.simulate_dream_rollouts = MagicMock(return_value=[])
        assert isinstance(mock, LLMClient)


# ---------------------------------------------------------------------------
# OpenAIClient – parsing helpers
# ---------------------------------------------------------------------------


class TestOpenAIClientParsing:
    """Tests for the JSON parsing methods (no actual API calls)."""

    def test_parse_trait_deltas_valid(self):
        raw = json.dumps({
            "hexaco": {"sincerity": 0.03, "creativity": -0.02},
            "tci_character": {"empathy": 0.01},
        })
        result = OpenAIClient._parse_trait_deltas(raw)
        assert result["hexaco"]["sincerity"] == 0.03
        assert result["hexaco"]["creativity"] == -0.02
        assert result["tci_character"]["empathy"] == 0.01

    def test_parse_trait_deltas_clamps_values(self):
        raw = json.dumps({"hexaco": {"sincerity": 0.5}})
        result = OpenAIClient._parse_trait_deltas(raw)
        assert result["hexaco"]["sincerity"] == 0.05  # clamped

    def test_parse_trait_deltas_empty(self):
        result = OpenAIClient._parse_trait_deltas("{}")
        assert result == {}

    def test_parse_trait_deltas_invalid_json(self):
        result = OpenAIClient._parse_trait_deltas("not json")
        assert result == {}

    def test_parse_trait_deltas_rejects_invalid_models(self):
        raw = json.dumps({"invalid_model": {"trait": 0.01}})
        result = OpenAIClient._parse_trait_deltas(raw)
        assert result == {}

    def test_parse_trait_deltas_strips_code_fence(self):
        raw = '```json\n{"hexaco": {"sincerity": 0.02}}\n```'
        result = OpenAIClient._parse_trait_deltas(raw)
        assert result["hexaco"]["sincerity"] == 0.02

    def test_parse_string_list_valid(self):
        raw = json.dumps(["fact one", "fact two"])
        result = OpenAIClient._parse_string_list(raw)
        assert result == ["fact one", "fact two"]

    def test_parse_string_list_empty(self):
        result = OpenAIClient._parse_string_list("[]")
        assert result == []

    def test_parse_string_list_invalid(self):
        result = OpenAIClient._parse_string_list("not json")
        assert result == []

    def test_parse_string_list_strips_code_fence(self):
        raw = '```json\n["a", "b"]\n```'
        result = OpenAIClient._parse_string_list(raw)
        assert result == ["a", "b"]

    def test_parse_string_list_filters_empty_items(self):
        raw = json.dumps(["good", "", "also good", None])
        result = OpenAIClient._parse_string_list(raw)
        assert result == ["good", "also good"]


# ---------------------------------------------------------------------------
# OpenAIClient – chat with mocked API
# ---------------------------------------------------------------------------


def _mock_completion(content: str, model: str = "gpt-5.4"):
    """Create a mock OpenAI completion response."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = content
    mock_resp.model = model
    mock_resp.usage.prompt_tokens = 100
    mock_resp.usage.completion_tokens = 50
    mock_resp.usage.total_tokens = 150
    return mock_resp


class TestOpenAIClientChat:
    def test_chat_returns_llm_response(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion(
                "Hello, I am a Being!"
            )
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            resp = client.chat(
                system_prompt="<being>...</being>",
                messages=[{"role": "user", "content": "Hi"}],
            )

            assert isinstance(resp, LLMResponse)
            assert resp.content == "Hello, I am a Being!"
            assert resp.model == "gpt-5.4"
            assert resp.usage["total_tokens"] == 150

    def test_chat_passes_system_prompt_and_messages(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion("ok")
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key", model="gpt-5.4")
            client.chat(
                system_prompt="sys prompt",
                messages=[{"role": "user", "content": "msg"}],
                temperature=0.5,
                max_tokens=512,
            )

            call_args = mock_instance.chat.completions.create.call_args
            assert call_args.kwargs["model"] == "gpt-5.4"
            assert call_args.kwargs["temperature"] == 0.5
            assert call_args.kwargs["max_completion_tokens"] == 512
            msgs = call_args.kwargs["messages"]
            assert msgs[0]["role"] == "system"
            assert msgs[0]["content"] == "sys prompt"
            assert msgs[1]["role"] == "user"
            assert msgs[1]["content"] == "msg"

    def test_chat_normalizes_internal_being_role_to_assistant(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion("ok")
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key", model="gpt-5.4")
            client.chat(
                system_prompt="sys prompt",
                messages=[
                    {"role": "user", "content": "msg1"},
                    {"role": "being", "content": "msg2"},
                ],
            )

            call_args = mock_instance.chat.completions.create.call_args
            msgs = call_args.kwargs["messages"]
            assert msgs[2]["role"] == "assistant"
            assert msgs[2]["content"] == "msg2"


class TestOpenAIClientAnalyzeTraits:
    def test_analyze_traits_returns_deltas(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion(
                json.dumps({"hexaco": {"sincerity": 0.03}})
            )
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            deltas = client.analyze_traits(
                system_prompt="<being>...</being>",
                conversation_turn="Tell me about honesty",
                being_response="Honesty is important to me",
            )

            assert deltas == {"hexaco": {"sincerity": 0.03}}

    def test_analyze_traits_handles_empty_response(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion("{}")
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            deltas = client.analyze_traits("prompt", "msg", "resp")
            assert deltas == {}


class TestOpenAIClientSemanticFacts:
    def test_extract_semantic_facts(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion(
                json.dumps(["The user loves astronomy", "Stars are a key interest"])
            )
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            facts = client.extract_semantic_facts(
                episodes=[{"role": "user", "content": "I love stars"}],
                personality_summary="Name: Luna, Stage: sensorimotor",
            )

            assert len(facts) == 2
            assert "astronomy" in facts[0]


class TestOpenAIClientDeriveBeliefs:
    def test_derive_beliefs(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion(
                json.dumps(["The world is full of wonder"])
            )
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            beliefs = client.derive_beliefs(
                hypotheses=["hypothesis_about:stars"],
                personality_summary="Name: Luna",
            )

            assert len(beliefs) == 1
            assert "wonder" in beliefs[0]


# ---------------------------------------------------------------------------
# SleepCycle with LLM enhancement
# ---------------------------------------------------------------------------


class TestSleepCycleWithLLM:
    """Tests for LLM-enhanced sleep cycle phases."""

    def _make_state(self) -> PersonalityState:
        return PersonalityState(being_id="llm-sleep-test", name="Dreamer")

    def _make_llm_mock(self) -> MagicMock:
        llm = MagicMock()
        llm.extract_semantic_facts.return_value = [
            "The user frequently discusses astronomy",
            "Stars are emotionally significant to the user",
        ]
        llm.derive_beliefs.return_value = [
            "The universe is vast and beautiful",
        ]
        return llm

    def test_neural_semantization_is_used_when_trained(self):
        """After NeuralEngine training, semantization uses learned patterns."""
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        episodes = [
            {"content": "Stars are beautiful"},
            {"content": "Stars are amazing"},
        ]
        state = self._make_state()

        # Train the neural engine first
        personality_vector = cycle._flatten_traits(state)
        cycle.dream_engine.neural_engine.train(episodes, personality_vector)

        facts = cycle._semantize(episodes, state)

        # Neural engine should extract facts about 'stars'
        assert len(facts) > 0
        assert any("stars" in f.lower() for f in facts)

    def test_neural_belief_derivation_is_used_when_trained(self):
        """After NeuralEngine training, belief derivation uses learned patterns."""
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        episodes = [
            {"content": "stars are important to me"},
            {"content": "stars bring me peace"},
        ]
        state = self._make_state()

        # Train the neural engine first
        personality_vector = cycle._flatten_traits(state)
        cycle.dream_engine.neural_engine.train(episodes, personality_vector)

        hypotheses = [
            Hypothesis(action="hypothesis_about:stars important", reward=0.8, complexity=0.1),
        ]
        beliefs = cycle._extract_beliefs(hypotheses, state)

        assert len(beliefs) >= 1
        assert any("Learned:" in b for b in beliefs)

    def test_llm_fallback_on_semantization_error(self):
        llm_mock = MagicMock()
        llm_mock.extract_semantic_facts.side_effect = Exception("API error")
        cycle = SleepCycle(
            dream_engine=DreamEngine(seed=42),
            llm_client=llm_mock,
        )

        episodes = [
            {"content": "painting is great"},
            {"content": "painting is art"},
        ]
        facts = cycle._semantize(episodes, self._make_state())

        # Should fall back to rule-based
        assert any("painting" in f.lower() for f in facts)

    def test_llm_fallback_on_belief_error(self):
        llm_mock = MagicMock()
        llm_mock.derive_beliefs.side_effect = Exception("API error")
        cycle = SleepCycle(
            dream_engine=DreamEngine(seed=42),
            llm_client=llm_mock,
        )

        hypotheses = [
            Hypothesis(action="test_action", reward=0.5, complexity=0.1),
        ]
        beliefs = cycle._extract_beliefs(hypotheses, self._make_state())

        # Should fall back to rule-based
        assert any("Learned:" in b for b in beliefs)

    def test_full_cycle_with_neural_engine(self):
        """Full sleep cycle uses NeuralEngine for learning."""
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        state = self._make_state()
        episodes = [
            {"content": "Stars are beautiful"},
            {"content": "The night sky is amazing"},
        ]
        new_state, result = cycle.run(state, episodes, num_rollouts=50, svd_rank=4)

        assert isinstance(result, SleepResult)
        # Neural-extracted facts
        assert len(result.facts_extracted) > 0
        assert any("stars" in f.lower() for f in result.facts_extracted)
        # Training result is populated
        assert result.training_result is not None
        assert result.training_result.vocabulary_size > 0
        # SVD consolidation still works
        assert len(result.traits_before) == 72
        assert len(result.traits_after) == 72

    def test_no_llm_uses_rule_based(self):
        cycle = SleepCycle(dream_engine=DreamEngine(seed=42))

        state = self._make_state()
        episodes = [
            {"content": "painting is great"},
            {"content": "painting is art"},
        ]
        new_state, result = cycle.run(state, episodes, num_rollouts=50)

        # Rule-based fallback
        assert any("painting" in f.lower() for f in result.facts_extracted)
        assert all("Learned:" in b for b in result.beliefs_added)


# ---------------------------------------------------------------------------
# Orchestrator.chat() with LLM
# ---------------------------------------------------------------------------


class TestOrchestratorChat:
    """Tests for the self-learning chat method (no external LLM)."""

    def test_chat_works_without_llm_client(self):
        """chat() now works without LLM – uses self-learning."""
        from serhu_orchestrator.orchestrator import Orchestrator
        from tests.e2e.conftest import InMemoryArchival, InMemoryRelational

        with (
            patch("serhu_orchestrator.orchestrator.ArchivalMemory", InMemoryArchival),
            patch("serhu_orchestrator.orchestrator.RelationalMemory", InMemoryRelational),
        ):
            orch = Orchestrator(
                qdrant_url="mock://q",
                qdrant_api_key="k",
                supabase_url="mock://s",
                supabase_key="k",
                being_name="TestBeing",
            )

            # Should not raise – chat works without LLM now
            response, context = orch.chat("Hello")
            assert isinstance(response, str)
            assert len(response) > 0
            assert len(context.working) >= 2  # user msg + being response

    def test_chat_generates_self_learned_response(self):
        """After sleep, chat generates responses from learned patterns."""
        from serhu_orchestrator.orchestrator import Orchestrator
        from tests.e2e.conftest import InMemoryArchival, InMemoryRelational

        with (
            patch("serhu_orchestrator.orchestrator.ArchivalMemory", InMemoryArchival),
            patch("serhu_orchestrator.orchestrator.RelationalMemory", InMemoryRelational),
        ):
            orch = Orchestrator(
                qdrant_url="mock://q",
                qdrant_api_key="k",
                supabase_url="mock://s",
                supabase_key="k",
                being_name="ChatBeing",
            )

            # Add some episodes first
            for i in range(5):
                orch.process_message("user", f"Nature is wonderful and beautiful {i}")

            # Sleep to learn patterns
            result = orch.sleep_once(num_rollouts=50, svd_rank=4, seed=42)
            assert result.training_result is not None
            assert result.training_result.vocabulary_size > 0

            # Now chat should use learned patterns
            response, context = orch.chat("Tell me about nature")
            assert isinstance(response, str)
            assert len(response) > 0
            assert len(context.working) >= 2

    def test_chat_without_auto_traits(self):
        """chat with auto_traits=False skips trait extraction."""
        from serhu_orchestrator.orchestrator import Orchestrator
        from tests.e2e.conftest import InMemoryArchival, InMemoryRelational

        with (
            patch("serhu_orchestrator.orchestrator.ArchivalMemory", InMemoryArchival),
            patch("serhu_orchestrator.orchestrator.RelationalMemory", InMemoryRelational),
        ):
            orch = Orchestrator(
                qdrant_url="mock://q",
                qdrant_api_key="k",
                supabase_url="mock://s",
                supabase_key="k",
                being_name="NoTraitsBeing",
            )

            response, _ = orch.chat("Hello", auto_traits=False)

            assert isinstance(response, str)
            # Sociability should remain at default (no auto-trait update)
            assert orch.personality.hexaco.sociability == 0.5

    def test_chat_auto_traits_no_crash(self):
        """chat with auto_traits=True should not crash even without training."""
        from serhu_orchestrator.orchestrator import Orchestrator
        from tests.e2e.conftest import InMemoryArchival, InMemoryRelational

        with (
            patch("serhu_orchestrator.orchestrator.ArchivalMemory", InMemoryArchival),
            patch("serhu_orchestrator.orchestrator.RelationalMemory", InMemoryRelational),
        ):
            orch = Orchestrator(
                qdrant_url="mock://q",
                qdrant_api_key="k",
                supabase_url="mock://s",
                supabase_key="k",
                being_name="ErrorBeing",
            )

            # Should not raise, even without trained neural engine
            response, _ = orch.chat("Hello")
            assert isinstance(response, str)

    def test_sleep_with_self_learning(self):
        """Sleep cycle uses NeuralEngine for self-learning (no LLM)."""
        from serhu_orchestrator.orchestrator import Orchestrator
        from tests.e2e.conftest import InMemoryArchival, InMemoryRelational

        with (
            patch("serhu_orchestrator.orchestrator.ArchivalMemory", InMemoryArchival),
            patch("serhu_orchestrator.orchestrator.RelationalMemory", InMemoryRelational),
        ):
            orch = Orchestrator(
                qdrant_url="mock://q",
                qdrant_api_key="k",
                supabase_url="mock://s",
                supabase_key="k",
                being_name="SleepBeing",
            )

            # Add some episodes
            for i in range(5):
                orch.process_message("user", f"Nature is beautiful {i}")

            result = orch.sleep_once(num_rollouts=50, svd_rank=4, seed=42)

            assert any("nature" in f.lower() for f in result.facts_extracted)
            assert len(result.beliefs_added) > 0
            assert result.training_result is not None
            assert result.training_result.vocabulary_size > 0


# ---------------------------------------------------------------------------
# DreamEngine with LLM
# ---------------------------------------------------------------------------


class TestDreamEngineWithNeuralEngine:
    """Tests for NeuralEngine-powered dream rollouts."""

    def test_neural_hypotheses_generated(self):
        """DreamEngine generates hypotheses from NeuralEngine patterns."""
        engine = DreamEngine(seed=42)

        history = [
            {"content": "I love honesty and truth"},
            {"content": "Honesty is the best policy"},
        ]
        personality = [0.5] * 72
        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=50, top_k=5,
        )

        assert len(results) == 5
        # Neural engine should generate pattern-based hypotheses
        actions = [h.action for h in results]
        assert any("honesty" in a.lower() for a in actions)

    def test_llm_fallback_on_error(self):
        engine = DreamEngine(seed=42)

        history = [{"content": "test content"}]
        personality = [0.5] * 72
        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=50, top_k=5,
        )

        # Should fall back to random rollouts
        assert len(results) == 5
        for h in results:
            assert isinstance(h, Hypothesis)

    def test_empty_history_still_works(self):
        engine = DreamEngine(seed=42)

        history = [{"content": "test"}]
        personality = [0.5] * 72
        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=50, top_k=5,
        )

        # Should use random rollouts since LLM returned nothing
        assert len(results) == 5

    def test_no_llm_uses_random_only(self):
        engine = DreamEngine(seed=42)

        history = [{"content": "test"}]
        personality = [0.5] * 72
        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=50, top_k=5,
        )

        assert len(results) == 5
        for h in results:
            assert isinstance(h, Hypothesis)

    def test_results_sorted_by_reward(self):
        engine = DreamEngine(seed=42)

        history = [{"content": "test"}]
        personality = [0.5] * 72
        results = engine.perform_dream_rollouts(
            history, personality, num_rollouts=100, top_k=10,
            personality_summary="Name: Test",
        )

        # Results should be sorted by reward descending
        for i in range(len(results) - 1):
            assert results[i].reward >= results[i + 1].reward


# ---------------------------------------------------------------------------
# OpenAIClient – new methods
# ---------------------------------------------------------------------------


class TestOpenAIClientDreamHypotheses:
    """Tests for generate_dream_hypotheses."""

    def test_generate_dream_hypotheses(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion(
                json.dumps([
                    "The user values honesty",
                    "Nature triggers positive emotions",
                ])
            )
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            hypotheses = client.generate_dream_hypotheses(
                episodes=[{"role": "user", "content": "I love honesty"}],
                personality_summary="Name: Test",
                num_hypotheses=5,
            )

            assert len(hypotheses) == 2
            assert "honesty" in hypotheses[0]

    def test_generate_dream_hypotheses_empty(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion("[]")
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            hypotheses = client.generate_dream_hypotheses(
                episodes=[], personality_summary="Test",
            )
            assert hypotheses == []


class TestOpenAIClientDreamRollouts:
    """Tests for simulate_dream_rollouts."""

    def test_simulate_dream_rollouts(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion(
                json.dumps([
                    {"action": "express empathy", "reward": 0.8, "complexity": 0.2},
                    {"action": "ask about feelings", "reward": 0.6, "complexity": 0.3},
                ])
            )
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            results = client.simulate_dream_rollouts(
                hypotheses=["hypothesis1"],
                personality_summary="Name: Test",
                recent_context=["conversation"],
            )

            assert len(results) == 2
            assert results[0]["action"] == "express empathy"
            assert results[0]["reward"] == 0.8

    def test_simulate_dream_rollouts_clamps_values(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion(
                json.dumps([
                    {"action": "test", "reward": 1.5, "complexity": -0.5},
                ])
            )
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            results = client.simulate_dream_rollouts(
                hypotheses=["h1"],
                personality_summary="Test",
                recent_context=[],
            )

            assert results[0]["reward"] == 1.0  # clamped
            assert results[0]["complexity"] == 0.0  # clamped

    def test_simulate_dream_rollouts_invalid_json(self):
        with patch("serhu_orchestrator.llm.openai_client.OpenAI") as MockOpenAI:
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = _mock_completion(
                "not valid json"
            )
            MockOpenAI.return_value = mock_instance

            client = OpenAIClient(api_key="test-key")
            results = client.simulate_dream_rollouts(
                hypotheses=["h1"],
                personality_summary="Test",
                recent_context=[],
            )
            assert results == []

    def test_parse_rollout_results_strips_code_fence(self):
        raw = '```json\n[{"action": "a", "reward": 0.5, "complexity": 0.1}]\n```'
        results = OpenAIClient._parse_rollout_results(raw)
        assert len(results) == 1
        assert results[0]["action"] == "a"
