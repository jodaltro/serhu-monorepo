"""Visual state types for the morphogenesis engine.

Defines the data structures that describe the Being's visual manifestation
in 3D space: color profile, geometry parameters, and animation state.

The visual state is derived from the Being's PersonalityState and evolves
as the Being's personality and cognitive development progress.

References:
    - Kiki/Bouba effect: https://en.wikipedia.org/wiki/Bouba/kiki_effect
    - Shape psychology: https://uxdesign.cc/the-psychology-behind-shapes-and-colors-17dd93ce08a2
    - Color-personality correlations: https://pmc.ncbi.nlm.nih.gov/articles/PMC9806338/
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ColorProfile(BaseModel):
    """HSL-based color profile for the Being's visual manifestation.

    Hue encodes the dominant personality dimension, saturation reflects
    arousal/excitement levels, and lightness captures valence (positive/negative).
    """

    hue: float = Field(
        default=0.0,
        ge=0.0,
        le=360.0,
        description="Dominant hue in degrees (0-360). Mapped from personality traits.",
    )
    saturation: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Saturation (0-1). High = excited/aroused states, Low = introspective.",
    )
    lightness: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Lightness (0-1). High = positive valence, Low = negative/serious.",
    )
    alpha: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Opacity (0-1). Newborn Beings start translucent.",
    )

    def to_css_hsl(self) -> str:
        """Return CSS-compatible ``hsla()`` string."""
        return (
            f"hsla({self.hue:.0f}, {self.saturation * 100:.0f}%, "
            f"{self.lightness * 100:.0f}%, {self.alpha:.2f})"
        )

    def to_rgb(self) -> tuple[int, int, int]:
        """Convert HSL to RGB (0-255)."""
        h = self.hue / 360.0
        s = self.saturation
        l_ = self.lightness

        if s == 0.0:
            r = g = b = l_
        else:
            def hue_to_rgb(p: float, q: float, t: float) -> float:
                if t < 0:
                    t += 1
                if t > 1:
                    t -= 1
                if t < 1 / 6:
                    return p + (q - p) * 6 * t
                if t < 1 / 2:
                    return q
                if t < 2 / 3:
                    return p + (q - p) * (2 / 3 - t) * 6
                return p

            q = l_ * (1 + s) if l_ < 0.5 else l_ + s - l_ * s
            p = 2 * l_ - q
            r = hue_to_rgb(p, q, h + 1 / 3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1 / 3)

        return (int(r * 255), int(g * 255), int(b * 255))


class GeometryProfile(BaseModel):
    """Geometry parameters for the Being's 3D mesh.

    Maps personality dimensions to shape characteristics following
    the Kiki/Bouba principle: agreeable/soft personalities produce
    rounded forms, while assertive/sharp personalities produce
    angular forms.
    """

    roundness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Overall roundness (0=angular, 1=spherical). Driven by Agreeableness.",
    )
    complexity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Geometric complexity (polygon count / fractal detail). Driven by cognitive age.",
    )
    symmetry: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Bilateral symmetry (0=asymmetric, 1=perfect symmetry). Driven by Conscientiousness.",
    )
    scale: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Overall size/scale. Grows with cognitive development.",
    )
    spikiness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Vertex displacement sharpness. Driven by Novelty Seeking / low Agreeableness.",
    )
    organic_noise: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Simplex noise amplitude for organic 'breathing'. Driven by Openness.",
    )


class AnimationParams(BaseModel):
    """Animation parameters for the Being's movement and effects.

    Derived from temperament dimensions: high Novelty Seeking produces
    fast, exploratory movement; high Harm Avoidance produces slow,
    cautious movement centered on screen.
    """

    pulse_rate: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Pulse/breathing rate in Hz. Driven by arousal level.",
    )
    movement_speed: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Movement speed through space (0=still, 1=fast). Driven by Novelty Seeking.",
    )
    center_attraction: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Attraction to screen center (0=exploratory, 1=stays centered). Driven by Harm Avoidance.",
    )
    glow_intensity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Glow/emission intensity. Driven by Extraversion liveliness.",
    )
    roughness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Surface roughness for PBR shaders (0=mirror/metallic, 1=matte/diffuse).",
    )


class VisualState(BaseModel):
    """Complete visual state for the Being at a point in time.

    This is the output of the morphogenesis engine: a complete description
    of how the Being should appear and move, suitable for consumption by
    a 3D renderer (Three.js, Unity, Unreal, etc.).
    """

    being_id: str = Field(description="Being identifier")
    color: ColorProfile = Field(default_factory=ColorProfile)
    geometry: GeometryProfile = Field(default_factory=GeometryProfile)
    animation: AnimationParams = Field(default_factory=AnimationParams)
    cognitive_stage: str = Field(
        default="sensorimotor",
        description="Current Piaget stage, for renderer-specific effects.",
    )
    cognitive_age: float = Field(
        default=0.0,
        ge=0.0,
        description="Cognitive age in months, for renderer interpolation.",
    )
