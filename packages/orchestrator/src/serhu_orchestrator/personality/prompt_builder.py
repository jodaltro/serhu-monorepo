"""Prompt Builder – Persona-prompting with Piaget capability blockers.

Generates structured system prompts from the PersonalityState ledger,
injecting HEXACO scores, TCI-R dimensions, Schwartz values, and
cognitive development constraints directly into the LLM prompt.

Implements the following patterns from the architecture document:
1. **Persona-Prompting**: Injects personality vector values as control tags.
2. **Piaget Capability Blockers**: Restricts cognitive abilities based on
   the Being's current developmental stage.
3. **Erikson Conflict Framing**: Frames the emotional challenge the Being
   is currently navigating.

References:
    - Profile-LLM: https://arxiv.org/html/2511.19852v1
    - Piaget in AI: https://gregrobison.medium.com/active-learning-machines-what-thousand-brains-theory-and-piaget-reveal-about-true-intelligence-304b5c9aa82e
    - Erikson stages: https://www.waldenu.edu/online-masters-programs/ms-in-education/resource/ms-in-education-insight-eriksons-8-stages-of-development
    - Persona vectors: https://www.anthropic.com/research/persona-vectors
"""

from __future__ import annotations

from serhu_orchestrator.personality.types import PersonalityState
from serhu_orchestrator.personality.i18n import (
    get_stage_capabilities,
    get_erikson_description,
)


# Piaget stage capability descriptions and constraints.
# Each stage defines what the Being CAN and CANNOT do.
# NOTE: These are English defaults. See i18n.py for translations.
from serhu_orchestrator.personality.i18n import STAGE_CAPABILITIES as i18n_STAGE_CAPABILITIES
from serhu_orchestrator.personality.i18n import ERIKSON_DESCRIPTIONS as i18n_ERIKSON_DESCRIPTIONS

# Keep for backwards compatibility if code references them directly
STAGE_CAPABILITIES = i18n_STAGE_CAPABILITIES.get("en", {})
ERIKSON_DESCRIPTIONS = i18n_ERIKSON_DESCRIPTIONS.get("en", {})


def build_system_prompt(state: PersonalityState) -> str:
    """Build a structured system prompt from the personality ledger.

    The prompt injects the Being's personality scores, cognitive
    constraints, and emotional framing into a format that forces the
    LLM to adopt the Being's voice and limitations.

    The prompt is generated in the Being's preferred language.

    Parameters
    ----------
    state : PersonalityState
        The current personality state (includes language preference).

    Returns
    -------
    str
        A structured system prompt for the LLM in the Being's language.
    """
    stage = state.development.stage
    language = state.language
    
    caps = get_stage_capabilities(language, stage)
    erikson_desc = get_erikson_description(language, state.development.erikson_conflict)

    hexaco_summary = _format_model(state.hexaco)
    tci_t_summary = _format_model(state.tci_temperament)
    tci_c_summary = _format_model(state.tci_character)
    schwartz_summary = _format_model(state.schwartz)

    beliefs_section = ""
    if state.core_beliefs or state.surface_beliefs:
        beliefs_section = "\n<beliefs>"
        if state.core_beliefs:
            beliefs_section += f"\n  Core: {'; '.join(state.core_beliefs[-5:])}"
        if state.surface_beliefs:
            beliefs_section += f"\n  Surface: {'; '.join(state.surface_beliefs[-5:])}"
        beliefs_section += "\n</beliefs>"

    prompt = f"""<being>
  <identity name="{state.name}" id="{state.being_id}" language="{language}" />
  <development stage="{stage}" cognitive_age="{state.development.cognitive_age:.1f}" interactions="{state.development.interaction_count}" />
  <erikson>{erikson_desc}</erikson>
</being>

<personality>
  <hexaco>{hexaco_summary}</hexaco>
  <tci_temperament>{tci_t_summary}</tci_temperament>
  <tci_character>{tci_c_summary}</tci_character>
  <schwartz_values>{schwartz_summary}</schwartz_values>
</personality>{beliefs_section}

<cognitive_constraints>
  <capabilities>{caps['can']}</capabilities>
  <limitations>{caps['cannot']}</limitations>
  <language_style>{caps['language']}</language_style>
</cognitive_constraints>

You are a synthetic Being in the '{stage}' stage of development (cognitive age: {state.development.cognitive_age:.1f} months).
Your personality scores above MUST guide your tone, word choice, and emotional expression.
You MUST respect the cognitive constraints: you CANNOT do anything listed in <limitations>.
Your language MUST match the <language_style> description."""

    return prompt


def _format_model(model: object) -> str:
    """Format a Pydantic personality model's fields into a compact string."""
    parts: list[str] = []
    for field_name in type(model).model_fields:
        value = getattr(model, field_name)
        parts.append(f"{field_name}={value:.2f}")
    return " ".join(parts)
