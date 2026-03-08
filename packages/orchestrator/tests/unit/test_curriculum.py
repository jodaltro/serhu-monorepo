"""Unit tests for the curriculum subsystem (World Seed, Episodes, Adaptive)."""

import pytest

from serhu_orchestrator.curriculum.types import (
    CurriculumConfig,
    EpisodeConstraints,
    FailureAnalysis,
    HumanWorldEnvelope,
    RewardScheme,
    SuccessCriterion,
    SyntheticEpisode,
    WorldSeedFact,
)
from serhu_orchestrator.curriculum.envelope import (
    ALL_DOMAINS,
    HUMAN_WORLD_ENVELOPE,
    Domain,
    get_all_stage_vocabulary,
    get_domain_names,
    get_stage_vocabulary,
)
from serhu_orchestrator.curriculum.world_seed import (
    get_world_seed,
    get_world_seed_facts,
)
from serhu_orchestrator.curriculum.episodes import (
    generate_synthetic_episodes,
)
from serhu_orchestrator.curriculum.adaptive import (
    generate_adaptive_episodes,
)
from serhu_orchestrator.personality.types import STAGE_ORDER


# ===========================================================================
# Types
# ===========================================================================


class TestWorldSeedFact:
    """Tests for WorldSeedFact Pydantic model."""

    def test_creation(self):
        f = WorldSeedFact(
            fact_id="test_001",
            stage="sensorimotor",
            domain="everyday_objects",
            fact="Objects exist even when hidden.",
            examples=["Ball under blanket"],
            counterexamples=["Sounds vanish"],
        )
        assert f.fact_id == "test_001"
        assert f.stage == "sensorimotor"
        assert f.domain == "everyday_objects"
        assert len(f.examples) == 1
        assert len(f.counterexamples) == 1

    def test_defaults(self):
        f = WorldSeedFact(
            fact_id="test_002",
            stage="preoperational",
            domain="communication",
            fact="Why asks for a reason.",
        )
        assert f.examples == []
        assert f.counterexamples == []


class TestSyntheticEpisode:
    """Tests for SyntheticEpisode Pydantic model."""

    def test_creation(self):
        ep = SyntheticEpisode(
            episode_id="ep_001",
            stage="sensorimotor",
            domain="everyday_objects",
            setting="User hides a ball.",
            user_turns=["Look!", "Where is it?"],
            expected_good_response="...ball?",
        )
        assert ep.episode_id == "ep_001"
        assert len(ep.user_turns) == 2
        assert ep.constraints.max_words is None
        assert ep.success_criteria == []
        assert ep.common_failure_modes == []

    def test_with_constraints(self):
        ep = SyntheticEpisode(
            episode_id="ep_002",
            stage="preoperational",
            domain="communication",
            setting="Color task.",
            user_turns=["What color is the sky?"],
            constraints=EpisodeConstraints(max_words=5, format="single_word"),
            expected_good_response="Blue!",
        )
        assert ep.constraints.max_words == 5
        assert ep.constraints.format == "single_word"


class TestFailureAnalysis:
    """Tests for FailureAnalysis model."""

    def test_creation(self):
        fa = FailureAnalysis(
            failure_id="f1",
            stage="sensorimotor",
            broken_criteria=["word_count"],
            failure_description="Responses too long",
        )
        assert fa.frequency == 1

    def test_frequency_min(self):
        with pytest.raises(Exception):
            FailureAnalysis(
                failure_id="f2",
                stage="sensorimotor",
                broken_criteria=["word_count"],
                failure_description="Test",
                frequency=0,
            )


class TestCurriculumConfig:
    """Tests for CurriculumConfig model."""

    def test_defaults(self):
        cfg = CurriculumConfig()
        assert cfg.language == "en"
        assert cfg.facts_per_stage == 100
        assert cfg.episodes_per_stage == 50
        assert cfg.adaptive_batch_size == 30
        assert cfg.target_stages == list(STAGE_ORDER)

    def test_custom_stages(self):
        cfg = CurriculumConfig(target_stages=["sensorimotor"])
        assert cfg.target_stages == ["sensorimotor"]


# ===========================================================================
# Human World Envelope
# ===========================================================================


class TestEnvelope:
    """Tests for the Human World Envelope domain ontology."""

    def test_has_6_domains(self):
        assert len(ALL_DOMAINS) == 6

    def test_domain_names(self):
        names = get_domain_names()
        assert "everyday_objects" in names
        assert "space_time" in names
        assert "physical_actions" in names
        assert "social_routines" in names
        assert "tasks_and_rules" in names
        assert "communication" in names

    def test_human_world_envelope_is_dict(self):
        assert isinstance(HUMAN_WORLD_ENVELOPE, dict)
        assert len(HUMAN_WORLD_ENVELOPE) == 6

    def test_domain_has_stage_vocabulary(self):
        for domain in ALL_DOMAINS:
            assert isinstance(domain.stage_vocabulary, dict)
            for stage in STAGE_ORDER:
                vocab = domain.stage_vocabulary.get(stage, [])
                assert isinstance(vocab, list)

    def test_get_stage_vocabulary(self):
        vocab = get_stage_vocabulary("everyday_objects", "sensorimotor")
        assert len(vocab) > 0
        assert "ball" in vocab
        assert "cup" in vocab

    def test_get_stage_vocabulary_unknown_domain(self):
        vocab = get_stage_vocabulary("nonexistent_domain", "sensorimotor")
        assert vocab == []

    def test_get_stage_vocabulary_unknown_stage(self):
        vocab = get_stage_vocabulary("everyday_objects", "nonexistent_stage")
        assert vocab == []

    def test_get_all_stage_vocabulary(self):
        all_vocab = get_all_stage_vocabulary("sensorimotor")
        assert len(all_vocab) == 6
        for domain_name, vocab in all_vocab.items():
            assert isinstance(vocab, list)

    def test_all_stages_have_vocabulary(self):
        for stage in STAGE_ORDER:
            for domain in ALL_DOMAINS:
                vocab = get_stage_vocabulary(domain.name, stage)
                assert len(vocab) > 0, f"{domain.name}/{stage} has no vocabulary"

    def test_vocabulary_complexity_increases_with_stage(self):
        """Later stages should have more abstract vocabulary."""
        simple_vocab = get_stage_vocabulary("tasks_and_rules", "sensorimotor")
        advanced_vocab = get_stage_vocabulary("tasks_and_rules", "formal_operational")
        # Formal has more abstract concepts like "algorithm", "strategy"
        assert "algorithm" in advanced_vocab or "strategy" in advanced_vocab
        assert "algorithm" not in simple_vocab


# ===========================================================================
# World Seed (Layer 1)
# ===========================================================================


class TestWorldSeed:
    """Tests for the World Seed fact generation."""

    def test_sensorimotor_facts(self):
        facts = get_world_seed("sensorimotor")
        assert len(facts) >= 40
        assert all(f.stage == "sensorimotor" for f in facts)

    def test_preoperational_facts(self):
        facts = get_world_seed("preoperational")
        assert len(facts) >= 40
        assert all(f.stage == "preoperational" for f in facts)

    def test_concrete_operational_facts(self):
        facts = get_world_seed("concrete_operational")
        assert len(facts) >= 30
        assert all(f.stage == "concrete_operational" for f in facts)

    def test_formal_operational_facts(self):
        facts = get_world_seed("formal_operational")
        assert len(facts) >= 30
        assert all(f.stage == "formal_operational" for f in facts)

    def test_unknown_stage_raises(self):
        with pytest.raises(ValueError, match="Unknown stage"):
            get_world_seed("nonexistent_stage")

    def test_facts_have_unique_ids(self):
        for stage in STAGE_ORDER:
            facts = get_world_seed(stage)
            ids = [f.fact_id for f in facts]
            assert len(ids) == len(set(ids)), f"Duplicate IDs in {stage}"

    def test_facts_have_examples(self):
        for stage in STAGE_ORDER:
            facts = get_world_seed(stage)
            with_examples = [f for f in facts if len(f.examples) > 0]
            assert len(with_examples) == len(facts), f"All {stage} facts should have examples"

    def test_facts_cover_all_domains(self):
        domain_names = get_domain_names()
        for stage in STAGE_ORDER:
            facts = get_world_seed(stage)
            domains_covered = {f.domain for f in facts}
            for d in domain_names:
                assert d in domains_covered, f"Stage {stage} missing domain {d}"

    def test_get_world_seed_facts_all(self):
        all_facts = get_world_seed_facts()
        assert len(all_facts) == 4
        for stage in STAGE_ORDER:
            assert stage in all_facts
            assert len(all_facts[stage]) > 0

    def test_get_world_seed_facts_subset(self):
        subset = get_world_seed_facts(["sensorimotor", "preoperational"])
        assert len(subset) == 2
        assert "sensorimotor" in subset
        assert "preoperational" in subset

    def test_fact_ids_contain_stage_prefix(self):
        for stage in STAGE_ORDER:
            facts = get_world_seed(stage)
            prefix = stage.split("_")[0]  # "sensorimotor", "preoperational", "concrete", "formal"
            for f in facts:
                assert f.fact_id.startswith(prefix), f"Fact {f.fact_id} should start with {prefix}"

    def test_sensorimotor_facts_are_concrete(self):
        """Sensorimotor facts should use simple, concrete language."""
        facts = get_world_seed("sensorimotor")
        for f in facts:
            # Should not use highly abstract terms
            assert "hypothesis" not in f.fact.lower()
            assert "algorithm" not in f.fact.lower()
            assert "metacognition" not in f.fact.lower()

    def test_formal_facts_are_abstract(self):
        """Formal operational facts should use abstract reasoning."""
        facts = get_world_seed("formal_operational")
        abstract_keywords = {"hypothesis", "abstract", "ethical", "strategy", "evaluate",
                             "perspective", "critical", "analogy", "probability", "optimize"}
        all_text = " ".join(f.fact.lower() for f in facts)
        found = abstract_keywords & set(all_text.split())
        assert len(found) >= 3, f"Formal facts should use abstract terms, found: {found}"


# ===========================================================================
# Synthetic Episodes (Layer 2)
# ===========================================================================


class TestSyntheticEpisodes:
    """Tests for synthetic episode generation."""

    def test_sensorimotor_episodes(self):
        episodes = generate_synthetic_episodes("sensorimotor", seed=42)
        assert len(episodes) >= 5
        assert all(ep.stage == "sensorimotor" for ep in episodes)

    def test_preoperational_episodes(self):
        episodes = generate_synthetic_episodes("preoperational", seed=42)
        assert len(episodes) >= 5
        assert all(ep.stage == "preoperational" for ep in episodes)

    def test_concrete_operational_episodes(self):
        episodes = generate_synthetic_episodes("concrete_operational", seed=42)
        assert len(episodes) >= 5
        assert all(ep.stage == "concrete_operational" for ep in episodes)

    def test_formal_operational_episodes(self):
        episodes = generate_synthetic_episodes("formal_operational", seed=42)
        assert len(episodes) >= 5
        assert all(ep.stage == "formal_operational" for ep in episodes)

    def test_unknown_stage_raises(self):
        with pytest.raises(ValueError, match="Unknown stage"):
            generate_synthetic_episodes("nonexistent")

    def test_episodes_have_unique_ids(self):
        for stage in STAGE_ORDER:
            episodes = generate_synthetic_episodes(stage, seed=42)
            ids = [ep.episode_id for ep in episodes]
            assert len(ids) == len(set(ids)), f"Duplicate IDs in {stage}"

    def test_episodes_have_user_turns(self):
        for stage in STAGE_ORDER:
            episodes = generate_synthetic_episodes(stage, seed=42)
            for ep in episodes:
                assert len(ep.user_turns) >= 1, f"Episode {ep.episode_id} needs user turns"

    def test_episodes_have_expected_response(self):
        for stage in STAGE_ORDER:
            episodes = generate_synthetic_episodes(stage, seed=42)
            for ep in episodes:
                assert len(ep.expected_good_response) > 0

    def test_episodes_have_reward_scheme(self):
        for stage in STAGE_ORDER:
            episodes = generate_synthetic_episodes(stage, seed=42)
            for ep in episodes:
                assert isinstance(ep.reward_scheme, RewardScheme)

    def test_sensorimotor_episodes_have_strict_word_limits(self):
        """Sensorimotor episodes should enforce very short responses."""
        episodes = generate_synthetic_episodes("sensorimotor", seed=42)
        for ep in episodes:
            if ep.constraints.max_words is not None:
                assert ep.constraints.max_words <= 5, (
                    f"Sensorimotor episode {ep.episode_id} max_words={ep.constraints.max_words} too high"
                )

    def test_seed_reproducibility(self):
        """Same seed should produce identical episodes."""
        eps1 = generate_synthetic_episodes("sensorimotor", seed=42)
        eps2 = generate_synthetic_episodes("sensorimotor", seed=42)
        assert len(eps1) == len(eps2)
        for a, b in zip(eps1, eps2):
            assert a.episode_id == b.episode_id

    def test_episodes_have_success_criteria(self):
        for stage in STAGE_ORDER:
            episodes = generate_synthetic_episodes(stage, seed=42)
            with_criteria = [ep for ep in episodes if len(ep.success_criteria) > 0]
            assert len(with_criteria) > 0, f"Stage {stage} should have episodes with success criteria"

    def test_episodes_have_failure_modes(self):
        for stage in STAGE_ORDER:
            episodes = generate_synthetic_episodes(stage, seed=42)
            with_failures = [ep for ep in episodes if len(ep.common_failure_modes) > 0]
            assert len(with_failures) > 0, f"Stage {stage} should have episodes with failure modes"


# ===========================================================================
# Adaptive Curriculum (Layer 3)
# ===========================================================================


class TestAdaptiveCurriculum:
    """Tests for adaptive episode generation based on failures."""

    def test_empty_failures(self):
        result = generate_adaptive_episodes([], batch_size=10, seed=42)
        assert result == []

    def test_word_count_failure(self):
        failures = [
            FailureAnalysis(
                failure_id="f1",
                stage="sensorimotor",
                broken_criteria=["word_count"],
                failure_description="Responses too long",
            ),
        ]
        episodes = generate_adaptive_episodes(failures, batch_size=10, seed=42)
        assert len(episodes) > 0
        assert all(ep.stage == "sensorimotor" for ep in episodes)
        # All should test word count
        for ep in episodes:
            assert any(c.check_type == "word_count" for c in ep.success_criteria)

    def test_contains_failure(self):
        failures = [
            FailureAnalysis(
                failure_id="f2",
                stage="preoperational",
                broken_criteria=["contains"],
                failure_description="Missing target words",
            ),
        ]
        episodes = generate_adaptive_episodes(failures, batch_size=10, seed=42)
        assert len(episodes) > 0
        assert all(ep.stage == "preoperational" for ep in episodes)

    def test_format_failure(self):
        failures = [
            FailureAnalysis(
                failure_id="f3",
                stage="concrete_operational",
                broken_criteria=["format"],
                failure_description="Wrong output format",
            ),
        ]
        episodes = generate_adaptive_episodes(failures, batch_size=10, seed=42)
        assert len(episodes) > 0

    def test_classification_failure(self):
        failures = [
            FailureAnalysis(
                failure_id="f4",
                stage="preoperational",
                broken_criteria=["classification"],
                failure_description="Misclassifications",
            ),
        ]
        episodes = generate_adaptive_episodes(failures, batch_size=10, seed=42)
        assert len(episodes) > 0

    def test_sequence_failure(self):
        failures = [
            FailureAnalysis(
                failure_id="f5",
                stage="concrete_operational",
                broken_criteria=["sequence"],
                failure_description="Wrong sequence order",
            ),
        ]
        episodes = generate_adaptive_episodes(failures, batch_size=10, seed=42)
        assert len(episodes) > 0

    def test_multiple_failures(self):
        failures = [
            FailureAnalysis(
                failure_id="f1",
                stage="sensorimotor",
                broken_criteria=["word_count"],
                failure_description="Too many words",
                frequency=3,
            ),
            FailureAnalysis(
                failure_id="f2",
                stage="preoperational",
                broken_criteria=["contains"],
                failure_description="Missing content",
                frequency=1,
            ),
        ]
        episodes = generate_adaptive_episodes(failures, batch_size=20, seed=42)
        assert len(episodes) > 0
        assert len(episodes) <= 20

    def test_batch_size_respected(self):
        failures = [
            FailureAnalysis(
                failure_id="f1",
                stage="sensorimotor",
                broken_criteria=["word_count"],
                failure_description="Too long",
                frequency=10,
            ),
        ]
        episodes = generate_adaptive_episodes(failures, batch_size=5, seed=42)
        assert len(episodes) <= 5

    def test_frequency_weighting(self):
        """Higher frequency failures should get more episodes."""
        failures = [
            FailureAnalysis(
                failure_id="f1",
                stage="sensorimotor",
                broken_criteria=["word_count"],
                failure_description="Too long",
                frequency=10,
            ),
            FailureAnalysis(
                failure_id="f2",
                stage="sensorimotor",
                broken_criteria=["format"],
                failure_description="Wrong format",
                frequency=1,
            ),
        ]
        episodes = generate_adaptive_episodes(failures, batch_size=30, seed=42)
        wc_count = sum(1 for ep in episodes if any(c.check_type == "word_count" for c in ep.success_criteria))
        fmt_count = sum(1 for ep in episodes if any(c.check_type == "format" for c in ep.success_criteria))
        # More word_count episodes due to higher frequency
        assert wc_count > fmt_count

    def test_unknown_criterion_ignored(self):
        """Unknown criterion types should be silently skipped."""
        failures = [
            FailureAnalysis(
                failure_id="f1",
                stage="sensorimotor",
                broken_criteria=["nonexistent_type"],
                failure_description="Unknown failure",
            ),
        ]
        episodes = generate_adaptive_episodes(failures, batch_size=10, seed=42)
        assert episodes == []

    def test_seed_reproducibility(self):
        failures = [
            FailureAnalysis(
                failure_id="f1",
                stage="sensorimotor",
                broken_criteria=["word_count"],
                failure_description="Test",
            ),
        ]
        eps1 = generate_adaptive_episodes(failures, batch_size=10, seed=42)
        eps2 = generate_adaptive_episodes(failures, batch_size=10, seed=42)
        assert len(eps1) == len(eps2)
        for a, b in zip(eps1, eps2):
            assert a.episode_id == b.episode_id
