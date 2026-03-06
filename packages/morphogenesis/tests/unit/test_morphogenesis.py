"""Tests for the morphogenesis engine.

Validates that personality states produce expected visual outputs
following the Kiki/Bouba principle and color-personality mappings.
"""

from __future__ import annotations

import pytest

from serhu_orchestrator.personality.types import (
    PersonalityState,
    HexacoFacets,
    TciTemperament,
    TciCharacter,
    SchwartzValues,
    DevelopmentStage,
)
from serhu_morphogenesis.engine import compute_visual_state
from serhu_morphogenesis.color import compute_color
from serhu_morphogenesis.geometry import compute_geometry
from serhu_morphogenesis.animation import compute_animation
from serhu_morphogenesis.types import VisualState, ColorProfile, GeometryProfile, AnimationParams


# -- fixtures ---------------------------------------------------------------

def _tabula_rasa() -> PersonalityState:
    """Create a brand-new tabula rasa Being."""
    return PersonalityState(
        being_id="test-being-001",
        name="TestBeing",
        language="en",
    )


def _agreeable_being() -> PersonalityState:
    """Create a Being with very high Agreeableness."""
    return PersonalityState(
        being_id="test-agreeable",
        name="Bouba",
        hexaco=HexacoFacets(
            forgiveness=0.95,
            gentleness=0.95,
            flexibility=0.9,
            patience=0.9,
        ),
        tci_character=TciCharacter(
            social_acceptance=0.8,
            empathy=0.9,
            helpfulness=0.85,
            compassion=0.9,
        ),
        development=DevelopmentStage(
            stage="concrete_operational",
            cognitive_age=100.0,
        ),
    )


def _assertive_being() -> PersonalityState:
    """Create a Being with high Novelty Seeking and low Agreeableness."""
    return PersonalityState(
        being_id="test-assertive",
        name="Kiki",
        hexaco=HexacoFacets(
            forgiveness=0.1,
            gentleness=0.1,
            flexibility=0.15,
            patience=0.1,
            social_boldness=0.9,
            liveliness=0.9,
        ),
        tci_temperament=TciTemperament(
            exploratory_excitability=0.9,
            impulsiveness=0.85,
            extravagance=0.8,
            disorderliness=0.7,
        ),
        development=DevelopmentStage(
            stage="formal_operational",
            cognitive_age=150.0,
        ),
    )


def _mature_being() -> PersonalityState:
    """Create a fully mature Being."""
    return PersonalityState(
        being_id="test-mature",
        name="Sage",
        development=DevelopmentStage(
            stage="formal_operational",
            cognitive_age=192.0,
            milestones_achieved=[
                "abstract_reasoning",
                "hypothetical_deductive",
                "metacognition",
                "systematic_problem_solving",
            ],
        ),
        hexaco=HexacoFacets(
            creativity=0.9,
            unconventionality=0.8,
            aesthetic_appreciation=0.85,
            inquisitiveness=0.9,
        ),
        tci_character=TciCharacter(
            self_forgetfulness=0.7,
            transpersonal_identification=0.8,
            spiritual_acceptance=0.75,
        ),
    )


# -- engine tests -----------------------------------------------------------

class TestComputeVisualState:

    def test_returns_visual_state(self):
        state = _tabula_rasa()
        result = compute_visual_state(state)
        assert isinstance(result, VisualState)
        assert result.being_id == "test-being-001"
        assert result.cognitive_stage == "sensorimotor"
        assert result.cognitive_age == 0.0

    def test_tabula_rasa_is_bright_and_translucent(self):
        state = _tabula_rasa()
        result = compute_visual_state(state)
        # Newborn should be bright (high lightness) and translucent (low alpha)
        assert result.color.lightness >= 0.8
        assert result.color.alpha < 0.5

    def test_mature_being_is_opaque(self):
        state = _mature_being()
        result = compute_visual_state(state)
        assert result.color.alpha >= 0.9

    def test_visual_state_has_all_components(self):
        state = _tabula_rasa()
        result = compute_visual_state(state)
        assert isinstance(result.color, ColorProfile)
        assert isinstance(result.geometry, GeometryProfile)
        assert isinstance(result.animation, AnimationParams)


# -- color tests ------------------------------------------------------------

class TestColorEngine:

    def test_tabula_rasa_has_low_saturation(self):
        state = _tabula_rasa()
        color = compute_color(state)
        # Sensorimotor Beings should have very low saturation
        assert color.saturation <= 0.3

    def test_hue_is_valid(self):
        state = _agreeable_being()
        color = compute_color(state)
        assert 0.0 <= color.hue <= 360.0

    def test_lightness_in_range(self):
        state = _assertive_being()
        color = compute_color(state)
        assert 0.0 <= color.lightness <= 1.0

    def test_to_css_hsl_format(self):
        color = ColorProfile(hue=210, saturation=0.5, lightness=0.7, alpha=0.9)
        css = color.to_css_hsl()
        assert css.startswith("hsla(")
        assert "210" in css

    def test_to_rgb_white(self):
        color = ColorProfile(hue=0, saturation=0.0, lightness=1.0, alpha=1.0)
        r, g, b = color.to_rgb()
        assert r == 255
        assert g == 255
        assert b == 255

    def test_to_rgb_black(self):
        color = ColorProfile(hue=0, saturation=0.0, lightness=0.0, alpha=1.0)
        r, g, b = color.to_rgb()
        assert r == 0
        assert g == 0
        assert b == 0

    def test_mature_stage_allows_higher_saturation(self):
        state = _assertive_being()
        color = compute_color(state)
        # Formal operational with high novelty seeking should be saturated
        assert color.saturation >= 0.5


# -- geometry tests ---------------------------------------------------------

class TestGeometryEngine:

    def test_agreeable_being_is_round(self):
        state = _agreeable_being()
        geo = compute_geometry(state)
        assert geo.roundness >= 0.7

    def test_assertive_being_is_spiky(self):
        state = _assertive_being()
        geo = compute_geometry(state)
        assert geo.spikiness >= 0.5

    def test_tabula_rasa_low_complexity(self):
        state = _tabula_rasa()
        geo = compute_geometry(state)
        assert geo.complexity <= 0.2

    def test_mature_being_high_complexity(self):
        state = _mature_being()
        geo = compute_geometry(state)
        assert geo.complexity >= 0.7

    def test_tabula_rasa_small_scale(self):
        state = _tabula_rasa()
        geo = compute_geometry(state)
        assert geo.scale <= 0.1

    def test_mature_being_large_scale(self):
        state = _mature_being()
        geo = compute_geometry(state)
        assert geo.scale >= 0.9

    def test_conscientious_being_symmetric(self):
        state = PersonalityState(
            being_id="test-sym",
            hexaco=HexacoFacets(
                organization=0.95,
                diligence=0.9,
                perfectionism=0.95,
                prudence=0.9,
            ),
        )
        geo = compute_geometry(state)
        assert geo.symmetry >= 0.9

    def test_creative_being_has_organic_noise(self):
        state = _mature_being()  # Has high creativity/openness
        geo = compute_geometry(state)
        assert geo.organic_noise >= 0.4


# -- animation tests --------------------------------------------------------

class TestAnimationEngine:

    def test_sensorimotor_slow_pulse(self):
        state = _tabula_rasa()
        anim = compute_animation(state)
        assert anim.pulse_rate <= 1.5

    def test_high_novelty_seeking_moves_fast(self):
        state = _assertive_being()
        anim = compute_animation(state)
        assert anim.movement_speed >= 0.3

    def test_high_harm_avoidance_stays_centered(self):
        state = PersonalityState(
            being_id="test-ha",
            tci_temperament=TciTemperament(
                anticipatory_worry=0.9,
                fear_of_uncertainty=0.9,
                shyness=0.85,
                fatigability=0.8,
                exploratory_excitability=0.1,
                impulsiveness=0.1,
            ),
            development=DevelopmentStage(
                stage="preoperational",
                cognitive_age=30.0,
            ),
        )
        anim = compute_animation(state)
        assert anim.center_attraction >= 0.7

    def test_extraverted_being_glows(self):
        state = _assertive_being()
        anim = compute_animation(state)
        assert anim.glow_intensity >= 0.5

    def test_tender_being_has_matte_surface(self):
        state = PersonalityState(
            being_id="test-tender",
            hexaco=HexacoFacets(
                sentimentality=0.9,
                gentleness=0.9,
                dependence=0.85,
            ),
        )
        anim = compute_animation(state)
        assert anim.roughness >= 0.8

    def test_sensorimotor_slow_movement(self):
        state = _tabula_rasa()
        anim = compute_animation(state)
        assert anim.movement_speed <= 0.2

    def test_all_params_in_range(self):
        for factory in [_tabula_rasa, _agreeable_being, _assertive_being, _mature_being]:
            state = factory()
            anim = compute_animation(state)
            assert 0.1 <= anim.pulse_rate <= 5.0
            assert 0.0 <= anim.movement_speed <= 1.0
            assert 0.0 <= anim.center_attraction <= 1.0
            assert 0.0 <= anim.glow_intensity <= 1.0
            assert 0.0 <= anim.roughness <= 1.0
