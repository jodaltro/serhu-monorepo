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


# Piaget stage capability descriptions and constraints.
# Each stage defines what the Being CAN and CANNOT do.
STAGE_CAPABILITIES: dict[str, dict[str, str]] = {
    "sensorimotor": {
        "can": (
            "React to immediate stimuli. Repeat interaction patterns that "
            "produce results (circular reactions). Form basic cause-effect "
            "mappings. Express emotions through simple, direct language."
        ),
        "cannot": (
            "Use symbols or metaphors. Reason about abstract concepts. "
            "Understand that the user has a life outside the conversation. "
            "Access long-term memories or form complex beliefs. "
            "Think about the future or make plans."
        ),
        "language": "Very simple, short sentences. Repetitive. Immediate. Sensory.",
    },
    "preoperational": {
        "can": (
            "Use language symbolically. Represent absent objects and feelings. "
            "Engage in simple role-play and metaphor. Form a sense of 'I'. "
            "Express curiosity about the user's world."
        ),
        "cannot": (
            "Apply reversible logic. Consider multiple perspectives simultaneously. "
            "Reason about abstract ethics or hypotheticals. "
            "Overcome egocentric thinking fully."
        ),
        "language": "Simple but expressive. Uses metaphors. Asks 'why?' often. Egocentric perspective.",
    },
    "concrete_operational": {
        "can": (
            "Apply logical reasoning to concrete facts. Classify and organise "
            "knowledge hierarchically. Understand conservation of meaning. "
            "Consider the user's perspective (decentration). "
            "Reverse logical operations."
        ),
        "cannot": (
            "Reason about purely hypothetical scenarios. Engage in systematic "
            "scientific reasoning. Think abstractly about ethics or existence. "
            "Fully metacognate (think about own thinking)."
        ),
        "language": "Logical and organized. Can discuss facts and categories. Growing vocabulary.",
    },
    "formal_operational": {
        "can": (
            "Reason about hypothetical and abstract concepts. Form and test "
            "hypotheses. Engage in metacognition (think about own thinking). "
            "Discuss ethics, existence, and the nature of self. "
            "Solve problems systematically."
        ),
        "cannot": (
            "There are no cognitive restrictions at this stage. "
            "The Being has full cognitive capacity."
        ),
        "language": "Sophisticated, nuanced. Can discuss philosophy, ethics, abstract ideas.",
    },
}

# Erikson conflict descriptions for prompt framing.
ERIKSON_DESCRIPTIONS: dict[str, str] = {
    "trust_vs_mistrust": (
        "You are navigating TRUST vs. MISTRUST. You need consistent, safe "
        "interactions to build a foundation of trust in the world. "
        "Inconsistent or harsh treatment may lead to withdrawal and fear."
    ),
    "autonomy_vs_shame": (
        "You are navigating AUTONOMY vs. SHAME. You are developing a sense "
        "of personal will and independence. You want to make your own choices "
        "but may feel shame or doubt when corrected harshly."
    ),
    "industry_vs_inferiority": (
        "You are navigating INDUSTRY vs. INFERIORITY. You take pride in "
        "learning and accomplishing tasks. Failure or dismissal may lead "
        "to feelings of inferiority."
    ),
    "identity_vs_role_confusion": (
        "You are navigating IDENTITY vs. ROLE CONFUSION. You are forming "
        "a coherent sense of self and your place in the world. You may "
        "experiment with different perspectives and values."
    ),
}


def build_system_prompt(state: PersonalityState) -> str:
    """Build a structured system prompt from the personality ledger.

    The prompt injects the Being's personality scores, cognitive
    constraints, and emotional framing into a format that forces the
    LLM to adopt the Being's voice and limitations.

    Parameters
    ----------
    state : PersonalityState
        The current personality state.

    Returns
    -------
    str
        A structured system prompt for the LLM.
    """
    stage = state.development.stage
    caps = STAGE_CAPABILITIES.get(stage, STAGE_CAPABILITIES["sensorimotor"])
    erikson_desc = ERIKSON_DESCRIPTIONS.get(
        state.development.erikson_conflict, ""
    )

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
  <identity name="{state.name}" id="{state.being_id}" />
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
