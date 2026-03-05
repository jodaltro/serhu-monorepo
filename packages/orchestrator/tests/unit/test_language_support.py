"""Unit tests for language support in personality and prompts."""

import pytest
from serhu_orchestrator.personality.types import PersonalityState
from serhu_orchestrator.personality.prompt_builder import build_system_prompt
from serhu_orchestrator.personality.i18n import (
    get_stage_capabilities,
    get_erikson_description,
    STAGE_CAPABILITIES,
    ERIKSON_DESCRIPTIONS,
)


class TestLanguageSupport:
    """Tests for multi-language personality support."""

    def test_personality_state_default_language(self):
        """PersonalityState defaults to English."""
        state = PersonalityState(being_id="test-123")
        assert state.language == "en"

    def test_personality_state_custom_language(self):
        """PersonalityState can be initialized with custom language."""
        for lang in ["en", "pt", "es", "fr"]:
            state = PersonalityState(being_id=f"test-{lang}", language=lang)
            assert state.language == lang

    def test_stage_capabilities_all_languages(self):
        """Stage capabilities exist for all supported languages."""
        supported_langs = ["en", "pt", "es", "fr"]
        stages = ["sensorimotor", "preoperational", "concrete_operational", "formal_operational"]

        for lang in supported_langs:
            assert lang in STAGE_CAPABILITIES, f"Language {lang} not in STAGE_CAPABILITIES"
            for stage in stages:
                caps = get_stage_capabilities(lang, stage)
                assert "can" in caps, f"Missing 'can' for {lang}/{stage}"
                assert "cannot" in caps, f"Missing 'cannot' for {lang}/{stage}"
                assert "language" in caps, f"Missing 'language' for {lang}/{stage}"
                assert len(caps["can"]) > 0, f"Empty 'can' for {lang}/{stage}"
                assert len(caps["cannot"]) > 0, f"Empty 'cannot' for {lang}/{stage}"
                assert len(caps["language"]) > 0, f"Empty 'language' for {lang}/{stage}"

    def test_erikson_descriptions_all_languages(self):
        """Erikson descriptions exist for all supported languages."""
        supported_langs = ["en", "pt", "es", "fr"]
        conflicts = [
            "trust_vs_mistrust",
            "autonomy_vs_shame",
            "industry_vs_inferiority",
            "identity_vs_role_confusion",
        ]

        for lang in supported_langs:
            assert lang in ERIKSON_DESCRIPTIONS, f"Language {lang} not in ERIKSON_DESCRIPTIONS"
            for conflict in conflicts:
                desc = get_erikson_description(lang, conflict)
                assert len(desc) > 0, f"Empty description for {lang}/{conflict}"

    def test_get_stage_capabilities_fallback(self):
        """get_stage_capabilities falls back to English for unknown language."""
        caps_unknown = get_stage_capabilities("xx", "sensorimotor")
        caps_en = get_stage_capabilities("en", "sensorimotor")
        assert caps_unknown == caps_en

    def test_get_erikson_description_fallback(self):
        """get_erikson_description falls back to English for unknown language."""
        desc_unknown = get_erikson_description("xx", "trust_vs_mistrust")
        desc_en = get_erikson_description("en", "trust_vs_mistrust")
        assert desc_unknown == desc_en

    def test_build_system_prompt_includes_language(self):
        """build_system_prompt includes language in the output."""
        for lang in ["en", "pt", "es", "fr"]:
            state = PersonalityState(being_id="test", language=lang)
            prompt = build_system_prompt(state)
            assert f'language="{lang}"' in prompt, f"Language {lang} not in prompt"

    def test_build_system_prompt_uses_language(self):
        """build_system_prompt uses language-specific content."""
        # Portuguese
        state_pt = PersonalityState(being_id="test-pt", language="pt")
        prompt_pt = build_system_prompt(state_pt)
        assert "Você está navegando" in prompt_pt  # Portuguese Erikson text

        # English
        state_en = PersonalityState(being_id="test-en", language="en")
        prompt_en = build_system_prompt(state_en)
        assert "You are navigating" in prompt_en  # English Erikson text

    def test_build_system_prompt_piaget_translated(self):
        """Piaget stage constraints are translated."""
        # Test Portuguese
        state_pt = PersonalityState(being_id="test-pt", language="pt")
        prompt_pt = build_system_prompt(state_pt)
        # Portuguese should have "Reagir" (react) instead of "React"
        assert "Reagir" in prompt_pt or "simples" in prompt_pt

        # Test English for comparison
        state_en = PersonalityState(being_id="test-en", language="en")
        prompt_en = build_system_prompt(state_en)
        assert "React" in prompt_en

    def test_language_persistence_in_personality(self):
        """Language is preserved in personality state."""
        state = PersonalityState(
            being_id="test-123",
            name="TestBeing",
            language="pt",
        )
        # Simulate saving and loading (this would go through the DB)
        state_dict = state.model_dump()
        new_state = PersonalityState(**state_dict)
        assert new_state.language == "pt"
