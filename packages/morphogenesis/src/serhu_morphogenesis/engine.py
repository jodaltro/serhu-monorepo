"""Morphogenesis engine — translates personality state to visual manifestation.

The main entry point for the visual transformation pipeline.  Accepts a
``PersonalityState`` and produces a ``VisualState`` that describes how
the Being should appear in 3D space.

Pipeline:
    PersonalityState
        → color.compute_color()    → ColorProfile
        → geometry.compute_geometry() → GeometryProfile
        → animation.compute_animation() → AnimationParams
        → VisualState (combined output for the renderer)

The engine is stateless: the same personality input always produces
the same visual output, allowing deterministic rendering and testing.

References:
    - Architecture spec: Morfogênese Visual section
    - Proc3D: https://arxiv.org/html/2601.12234v1
    - Color-personality: https://pmc.ncbi.nlm.nih.gov/articles/PMC9806338/
    - Shape psychology: https://uxdesign.cc/the-psychology-behind-shapes-and-colors-17dd93ce08a2
"""

from __future__ import annotations

from serhu_orchestrator.personality.types import PersonalityState

from serhu_morphogenesis.types import VisualState
from serhu_morphogenesis.color import compute_color
from serhu_morphogenesis.geometry import compute_geometry
from serhu_morphogenesis.animation import compute_animation


def compute_visual_state(state: PersonalityState) -> VisualState:
    """Compute the complete visual state for a Being.

    Parameters
    ----------
    state : PersonalityState
        The Being's current personality ledger.

    Returns
    -------
    VisualState
        Complete visual description for the 3D renderer.
    """
    return VisualState(
        being_id=state.being_id,
        color=compute_color(state),
        geometry=compute_geometry(state),
        animation=compute_animation(state),
        cognitive_stage=state.development.stage,
        cognitive_age=state.development.cognitive_age,
    )
