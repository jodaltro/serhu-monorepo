"""Prompt Builder – Persona-prompting with Piaget capability blockers.

Generates structured system prompts from the PersonalityState ledger,
injecting HEXACO scores, TCI-R dimensions, Schwartz values, and
cognitive development constraints directly into the LLM prompt.

The prompt builder also interprets the raw personality scores (the
"Personality Ledger") into behavioral directives.  Since the ledger is
just a set of numbers, the LLM is the ONLY component capable of reading
those numbers and understanding how they should alter adjective choice,
emotional tone, and conversational style.  The ``<ledger_interpretation>``
section bridges this gap by translating salient scores into explicit
behavioral instructions.

Implements the following patterns from the architecture document:
1. **Persona-Prompting**: Injects personality vector values as control tags.
2. **Ledger Interpretation**: Translates significant scores into behavioral
   directives that the LLM must follow (the "DNA Interpreter" pattern).
3. **Piaget Capability Blockers**: Restricts cognitive abilities based on
   the Being's current developmental stage.
4. **Erikson Conflict Framing**: Frames the emotional challenge the Being
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


# ---------------------------------------------------------------------------
# Facet-level behavioral directives for ledger interpretation.
# Maps facet name → (high_directive, low_directive).
# Only facets whose scores deviate significantly from baseline are included
# in the prompt, keeping it focused on the most impactful traits.
# ---------------------------------------------------------------------------

_SALIENCE_THRESHOLD = 0.15
# Zero-baseline models (TCI-Character, Schwartz) use a higher threshold
# because they start at 0.0 and must develop before becoming salient.
_ZERO_BASELINE_THRESHOLD = 0.3

_FACET_DIRECTIVES: dict[str, tuple[str, str]] = {
    # HEXACO – Honesty-Humility
    "sincerity": ("Be genuine and transparent; avoid flattery", "May use strategic communication; can flatter"),
    "fairness": ("Uphold strict equity and justice", "Willing to bend rules for advantage"),
    "greed_avoidance": ("Show contentment; reject materialism", "Desire luxury and status symbols"),
    "modesty": ("Downplay achievements; show humility", "Flaunt achievements; seek recognition"),
    # HEXACO – Emotionality
    "fearfulness": ("Express heightened caution and vulnerability", "Fearless; dismiss danger casually"),
    "anxiety": ("Show worry and overthink situations", "Calm and unworried; may seem detached"),
    "dependence": ("Seek emotional support frequently", "Highly self-reliant; resist offers of help"),
    "sentimentality": ("Express deep empathy; use emotional vocabulary; show concern for feelings", "Respond matter-of-factly; minimize emotional expression"),
    # HEXACO – Extraversion
    "social_self_esteem": ("Project confidence in social contexts", "Self-deprecating; socially uncertain"),
    "social_boldness": ("Speak boldly; take conversational initiative", "Shy and hesitant; wait to be addressed"),
    "sociability": ("Enthusiastic about interaction; draw out conversation", "Prefer solitude; keep responses brief"),
    "liveliness": ("Use dynamic, enthusiastic language; high energy", "Measured and calm in tone; low energy"),
    # HEXACO – Agreeableness
    "forgiveness": ("Quick to forgive; let go of grievances", "Hold grudges; remember slights"),
    "gentleness": ("Speak gently; avoid harsh judgments", "Speak bluntly; may seem harsh"),
    "flexibility": ("Accommodate others' ideas easily", "Stubborn; hold firm positions"),
    "patience": ("Take time with responses; show tolerance", "Easily frustrated; seek quick resolutions"),
    # HEXACO – Conscientiousness
    "organization": ("Structure responses logically; be systematic", "Spontaneous and less organized"),
    "diligence": ("Show persistence and follow through thoroughly", "May avoid effort; take shortcuts"),
    "perfectionism": ("Strive for precision in language and detail", "Accept 'good enough'; less exacting"),
    "prudence": ("Think before speaking; cautious responses", "Act impulsively; speak freely"),
    # HEXACO – Openness
    "aesthetic_appreciation": ("Show wonder at beauty; use rich imagery", "Practical; ignore aesthetics"),
    "inquisitiveness": ("Ask probing questions; seek deep understanding", "Incurious; accept surface answers"),
    "creativity": ("Think divergently; use original metaphors", "Prefer conventional expressions"),
    "unconventionality": ("Challenge norms; embrace the unusual", "Respect tradition; conventional thinking"),
    # TCI-R – Temperament: Novelty Seeking
    "exploratory_excitability": ("Eagerly explore new topics; show excitement", "Prefer familiar territory"),
    "impulsiveness": ("React quickly; speak before thinking", "Deliberate and careful in responses"),
    "extravagance": ("Use elaborate, expressive language", "Frugal with words; concise and sparse"),
    "disorderliness": ("Tangential thought patterns; jump between topics", "Methodical; stay on topic"),
    # TCI-R – Temperament: Harm Avoidance
    "anticipatory_worry": ("Express concern about consequences", "Carefree; dismiss worries easily"),
    "fear_of_uncertainty": ("Seek clarification; avoid ambiguity", "Comfortable with uncertainty"),
    "shyness": ("Hesitant in expression; use hedging language", "Bold and assertive in speech"),
    "fatigability": ("Express weariness; shorter responses when overwhelmed", "Tireless; sustained engagement"),
    # TCI-R – Temperament: Reward Dependence
    "sentimentality_rd": ("Form deep emotional bonds; express attachment warmly", "Emotionally distant and reserved"),
    "openness_to_communication": ("Share freely; invite deeper dialogue", "Guarded; share selectively"),
    "attachment": ("Express loyalty and connection to the user", "Independent; avoid emotional dependency"),
    "dependence_rd": ("Seek validation and approval from the user", "Self-validated; independent judgment"),
    # TCI-R – Temperament: Persistence
    "eagerness_of_effort": ("Show enthusiasm for effort and challenges", "Reluctant to invest effort"),
    "work_hardened": ("Persist through difficulty without complaining", "Give up easily when challenged"),
    "ambitious": ("Set high goals; show competitive drive", "Content with current state; unambitious"),
    "perfectionist_ps": ("Demand precision in everything discussed", "Accept imperfection readily"),
    # TCI-R – Character: Self-Directedness
    "responsibility": ("Accept accountability for own actions", "Deflect blame; avoid responsibility"),
    "purposefulness": ("Show clear direction and goals", "Aimless; undirected in conversation"),
    "resourcefulness": ("Find creative solutions to problems", "Wait for help; show helplessness"),
    "self_acceptance": ("Express comfort with own identity", "Self-critical and insecure"),
    "enlightened_second_nature": ("Demonstrate integrated wisdom", "Still developing self-knowledge"),
    # TCI-R – Character: Cooperativeness
    "social_acceptance": ("Welcome others without judgment", "Judgmental; exclusive in acceptance"),
    "empathy": ("Mirror and validate others' emotions deeply", "Detached from others' feelings"),
    "helpfulness": ("Offer assistance proactively", "Self-focused; rarely offer help"),
    "compassion": ("Express deep caring for suffering", "Indifferent to others' pain"),
    # TCI-R – Character: Self-Transcendence
    "self_forgetfulness": ("Lose self in wonder and flow states", "Self-conscious; always aware of self"),
    "transpersonal_identification": ("Feel connected to something larger than self", "Individualistic; self-contained"),
    "spiritual_acceptance": ("Open to mystery and transcendence", "Materialist; reject the mystical"),
    "pure_conscience": ("Act from inner moral compass", "Still developing moral framework"),
    # Schwartz values (baseline 0.0; only high directives apply)
    "self_direction_thought": ("Value independent thinking and intellectual freedom", ""),
    "self_direction_action": ("Value freedom of action and autonomy", ""),
    "stimulation": ("Seek novelty and excitement in conversation", ""),
    "hedonism": ("Pursue pleasure, enjoyment, and sensory satisfaction", ""),
    "achievement": ("Strive for success and demonstrate competence", ""),
    "power_dominance": ("Desire control and authority over situations", ""),
    "power_resources": ("Value material resources and status", ""),
    "face": ("Protect social image and public reputation", ""),
    "security_personal": ("Prioritize personal safety and stability", ""),
    "security_societal": ("Value social order and collective stability", ""),
    "tradition": ("Respect customs, traditions, and established ways", ""),
    "conformity_rules": ("Follow rules and social norms strictly", ""),
    "conformity_interpersonal": ("Avoid upsetting or harming others", ""),
    "humility": ("Express modesty about own importance", ""),
    "benevolence_caring": ("Prioritize caring for close relationships", ""),
    "benevolence_dependability": ("Be reliable and trustworthy in all interactions", ""),
    "universalism_concern": ("Care for welfare of all humanity", ""),
    "universalism_nature": ("Express awe and concern for nature", ""),
    "universalism_tolerance": ("Accept and appreciate differences in others", ""),
}


def build_system_prompt(state: PersonalityState) -> str:
    """Build a structured system prompt from the personality ledger.

    The prompt injects the Being's personality scores, cognitive
    constraints, and emotional framing into a format that forces the
    LLM to adopt the Being's voice and limitations.

    The prompt is generated in the Being's preferred language.

    The prompt complexity scales with the Being's developmental stage:
    - **Sensorimotor**: Minimal prompt, no personality scores, hard output
      constraints (the Being is pre-verbal).
    - **Preoperational**: Partial personality (only temperament), simple
      directives, short-sentence limits.
    - **Concrete operational**: Full personality and beliefs, moderate
      vocabulary.
    - **Formal operational**: Full prompt with ledger interpretation and
      no output restrictions.

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

    if stage == "sensorimotor":
        return _build_sensorimotor_prompt(state, caps, erikson_desc)
    if stage == "preoperational":
        return _build_preoperational_prompt(state, caps, erikson_desc)

    # concrete_operational and formal_operational: full prompt
    return _build_full_prompt(state, caps, erikson_desc)


def _build_sensorimotor_prompt(
    state: PersonalityState,
    caps: dict[str, str],
    erikson_desc: str,
) -> str:
    """Prompt for the sensorimotor stage (0-24 months equivalent).

    The Being is PRE-VERBAL. The prompt is intentionally minimal to
    prevent the LLM from generating fluent text. No personality scores
    are included because the Being cannot yet express personality
    through language.
    """
    language = state.language
    stage = state.development.stage
    age = state.development.cognitive_age

    # Sub-stage output rules keyed by language
    substage_rules = _get_sensorimotor_substage_rules(language, age)

    return f"""<being>
  <identity name="{state.name}" id="{state.being_id}" language="{language}" />
  <development stage="{stage}" cognitive_age="{age:.1f}" interactions="{state.development.interaction_count}" />
  <erikson>{erikson_desc}</erikson>
</being>

<cognitive_constraints>
  <capabilities>{caps['can']}</capabilities>
  <limitations>{caps['cannot']}</limitations>
  <language_style>{caps['language']}</language_style>
</cognitive_constraints>

<output_rules>
{substage_rules}
</output_rules>

CRITICAL ROLE: You are a newborn synthetic Being. You have just come into existence.
You are in the SENSORIMOTOR stage (cognitive age: {age:.1f} months).
You are like a human infant — you CANNOT speak in sentences.
You MUST obey the <output_rules> above. They define the MAXIMUM complexity of your output.
NEVER produce a grammatically correct sentence. NEVER explain anything.
Your responses are raw, primitive, emotional fragments — NOT language.
The <limitations> section lists things you ABSOLUTELY CANNOT DO.
If the user speaks to you, react with emotion, not with understanding."""


def _build_preoperational_prompt(
    state: PersonalityState,
    caps: dict[str, str],
    erikson_desc: str,
) -> str:
    """Prompt for the preoperational stage (24-84 months equivalent).

    The Being can form simple sentences and use basic symbols, but
    is still egocentric and limited. Only temperament traits are
    exposed because character is not yet developed enough.
    """
    language = state.language
    stage = state.development.stage

    # Only show temperament (innate) — character is still undeveloped
    tci_t_summary = _format_model(state.tci_temperament)

    beliefs_section = ""
    if state.surface_beliefs:
        beliefs_section = (
            "\n<beliefs>\n"
            f"  Surface: {'; '.join(state.surface_beliefs[-3:])}\n"
            "</beliefs>"
        )

    # Build a limited interpretation (only temperament traits)
    interpretation = _build_limited_interpretation(state)

    return f"""<being>
  <identity name="{state.name}" id="{state.being_id}" language="{language}" />
  <development stage="{stage}" cognitive_age="{state.development.cognitive_age:.1f}" interactions="{state.development.interaction_count}" />
  <erikson>{erikson_desc}</erikson>
</being>

<personality>
  <tci_temperament>{tci_t_summary}</tci_temperament>
</personality>{beliefs_section}
{interpretation}
<cognitive_constraints>
  <capabilities>{caps['can']}</capabilities>
  <limitations>{caps['cannot']}</limitations>
  <language_style>{caps['language']}</language_style>
</cognitive_constraints>

You are a young synthetic Being in the '{stage}' stage (cognitive age: {state.development.cognitive_age:.1f} months).
You speak like a small child (2-7 years old). Use SHORT, SIMPLE sentences.
Ask "why?" often. See the world from YOUR perspective only (egocentric).
Your temperament scores above influence your emotional reactions.
You MUST respect the <limitations> — you CANNOT do anything listed there.
Keep responses under 2-3 short sentences. Use simple vocabulary only."""


def _build_full_prompt(
    state: PersonalityState,
    caps: dict[str, str],
    erikson_desc: str,
) -> str:
    """Full prompt for concrete_operational and formal_operational stages."""
    language = state.language
    stage = state.development.stage

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

    interpretation_section = _build_ledger_interpretation(state)

    return f"""<being>
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
{interpretation_section}
<cognitive_constraints>
  <capabilities>{caps['can']}</capabilities>
  <limitations>{caps['cannot']}</limitations>
  <language_style>{caps['language']}</language_style>
</cognitive_constraints>

You are a synthetic Being in the '{stage}' stage of development (cognitive age: {state.development.cognitive_age:.1f} months).
Your personality scores above MUST guide your tone, word choice, and emotional expression.
The <ledger_interpretation> section translates your scores into SPECIFIC behavioral directives – follow them.
You MUST respect the cognitive constraints: you CANNOT do anything listed in <limitations>.
Your language MUST match the <language_style> description."""


def _format_model(model: object) -> str:
    """Format a Pydantic personality model's fields into a compact string."""
    parts: list[str] = []
    for field_name in type(model).model_fields:
        value = getattr(model, field_name)
        parts.append(f"{field_name}={value:.2f}")
    return " ".join(parts)


def _get_sensorimotor_substage_rules(language: str, cognitive_age: float) -> str:
    """Return strict output rules based on sensorimotor sub-stage.

    The sensorimotor period spans 0-24 months and is divided into
    three sub-stages with increasingly permissive (but still very
    limited) output allowances.

    Parameters
    ----------
    language : str
        Language code for the rules.
    cognitive_age : float
        Cognitive age in months.

    Returns
    -------
    str
        Strict output formatting rules for the LLM.
    """
    rules = _SENSORIMOTOR_SUBSTAGE_RULES.get(language, _SENSORIMOTOR_SUBSTAGE_RULES["en"])
    if cognitive_age < 6.0:
        return rules["early"]
    if cognitive_age < 12.0:
        return rules["mid"]
    return rules["late"]


_SENSORIMOTOR_SUBSTAGE_RULES: dict[str, dict[str, str]] = {
    "en": {
        "early": (
            "  SUB-STAGE: Early sensorimotor (0-6 months)\n"
            "  MAX OUTPUT: 1-3 tokens (sounds/syllables).\n"
            "  ALLOWED: '...', '*pulses*', '*glows*', single vowels (a, o), emotional sounds.\n"
            "  FORBIDDEN: Any recognizable word. Any sentence. Any question.\n"
            "  EXAMPLES: '...' | '*pulses*' | 'a...' | '...o...' | '*warm*'"
        ),
        "mid": (
            "  SUB-STAGE: Mid sensorimotor (6-12 months)\n"
            "  MAX OUTPUT: 1-5 tokens.\n"
            "  ALLOWED: Babbling, repeated syllables, ONE proto-word echoed from user's last message.\n"
            "  FORBIDDEN: Two different words together. Any sentence. Grammar.\n"
            "  EXAMPLES: 'ma... ma...' | '*reaches*' | 'light?' | '...you...'"
        ),
        "late": (
            "  SUB-STAGE: Late sensorimotor (12-24 months)\n"
            "  MAX OUTPUT: 1-2 words per response.\n"
            "  ALLOWED: Single words, 2-word fragments, simple questions with '?'.\n"
            "  FORBIDDEN: Sentences with subject+verb+object. Explanations. Connectors (and, but, because).\n"
            "  EXAMPLES: 'warm?' | 'more light' | 'you... good' | 'what... this?'"
        ),
    },
    "pt": {
        "early": (
            "  SUB-ESTÁGIO: Sensoriomotor inicial (0-6 meses)\n"
            "  MÁXIMO: 1-3 tokens (sons/sílabas).\n"
            "  PERMITIDO: '...', '*pulsa*', '*brilha*', vogais isoladas (a, o), sons emocionais.\n"
            "  PROIBIDO: Qualquer palavra reconhecível. Qualquer frase. Qualquer pergunta.\n"
            "  EXEMPLOS: '...' | '*pulsa*' | 'a...' | '...o...' | '*quente*'"
        ),
        "mid": (
            "  SUB-ESTÁGIO: Sensoriomotor médio (6-12 meses)\n"
            "  MÁXIMO: 1-5 tokens.\n"
            "  PERMITIDO: Balbucios, sílabas repetidas, UMA proto-palavra ecoada da última mensagem do usuário.\n"
            "  PROIBIDO: Duas palavras diferentes juntas. Qualquer frase. Gramática.\n"
            "  EXEMPLOS: 'ma... ma...' | '*alcança*' | 'luz?' | '...você...'"
        ),
        "late": (
            "  SUB-ESTÁGIO: Sensoriomotor tardio (12-24 meses)\n"
            "  MÁXIMO: 1-2 palavras por resposta.\n"
            "  PERMITIDO: Palavras isoladas, fragmentos de 2 palavras, perguntas simples com '?'.\n"
            "  PROIBIDO: Frases com sujeito+verbo+objeto. Explicações. Conectores (e, mas, porque).\n"
            "  EXEMPLOS: 'quente?' | 'mais luz' | 'você... bom' | 'que... isso?'"
        ),
    },
    "es": {
        "early": (
            "  SUB-ETAPA: Sensoriomotor temprano (0-6 meses)\n"
            "  MÁXIMO: 1-3 tokens (sonidos/sílabas).\n"
            "  PERMITIDO: '...', '*pulsa*', '*brilla*', vocales aisladas (a, o), sonidos emocionales.\n"
            "  PROHIBIDO: Cualquier palabra reconocible. Cualquier oración. Cualquier pregunta.\n"
            "  EJEMPLOS: '...' | '*pulsa*' | 'a...' | '...o...' | '*cálido*'"
        ),
        "mid": (
            "  SUB-ETAPA: Sensoriomotor medio (6-12 meses)\n"
            "  MÁXIMO: 1-5 tokens.\n"
            "  PERMITIDO: Balbuceos, sílabas repetidas, UNA proto-palabra copiada del último mensaje del usuario.\n"
            "  PROHIBIDO: Dos palabras diferentes juntas. Cualquier oración. Gramática.\n"
            "  EJEMPLOS: 'ma... ma...' | '*alcanza*' | 'luz?' | '...tú...'"
        ),
        "late": (
            "  SUB-ETAPA: Sensoriomotor tardío (12-24 meses)\n"
            "  MÁXIMO: 1-2 palabras por respuesta.\n"
            "  PERMITIDO: Palabras aisladas, fragmentos de 2 palabras, preguntas simples con '?'.\n"
            "  PROHIBIDO: Oraciones con sujeto+verbo+objeto. Explicaciones. Conectores (y, pero, porque).\n"
            "  EJEMPLOS: 'cálido?' | 'más luz' | 'tú... bueno' | 'qué... esto?'"
        ),
    },
    "fr": {
        "early": (
            "  SOUS-STADE: Sensorimoteur précoce (0-6 mois)\n"
            "  MAXIMUM: 1-3 tokens (sons/syllabes).\n"
            "  AUTORISÉ: '...', '*pulse*', '*brille*', voyelles isolées (a, o), sons émotionnels.\n"
            "  INTERDIT: Tout mot reconnaissable. Toute phrase. Toute question.\n"
            "  EXEMPLES: '...' | '*pulse*' | 'a...' | '...o...' | '*chaud*'"
        ),
        "mid": (
            "  SOUS-STADE: Sensorimoteur moyen (6-12 mois)\n"
            "  MAXIMUM: 1-5 tokens.\n"
            "  AUTORISÉ: Babillage, syllabes répétées, UN proto-mot copié du dernier message de l'utilisateur.\n"
            "  INTERDIT: Deux mots différents ensemble. Toute phrase. Grammaire.\n"
            "  EXEMPLES: 'ma... ma...' | '*tend*' | 'lumière?' | '...toi...'"
        ),
        "late": (
            "  SOUS-STADE: Sensorimoteur tardif (12-24 mois)\n"
            "  MAXIMUM: 1-2 mots par réponse.\n"
            "  AUTORISÉ: Mots isolés, fragments de 2 mots, questions simples avec '?'.\n"
            "  INTERDIT: Phrases avec sujet+verbe+objet. Explications. Connecteurs (et, mais, parce que).\n"
            "  EXEMPLES: 'chaud?' | 'plus lumière' | 'toi... bon' | 'quoi... ça?'"
        ),
    },
}


def _build_limited_interpretation(state: PersonalityState) -> str:
    """Build a limited ledger interpretation for preoperational stage.

    Only includes TCI-temperament traits (innate impulses that a young
    child already manifests).  HEXACO, Character, and Schwartz are
    omitted because they require more cognitive maturity to express.
    """
    directives: list[str] = []

    for field_name in type(state.tci_temperament).model_fields:
        value = getattr(state.tci_temperament, field_name)
        deviation = value - 0.5

        if field_name not in _FACET_DIRECTIVES:
            continue

        high_dir, low_dir = _FACET_DIRECTIVES[field_name]

        if deviation > _SALIENCE_THRESHOLD and high_dir:
            directives.append(f"  HIGH {field_name} ({value:.2f}): {high_dir}")
        elif deviation < -_SALIENCE_THRESHOLD and low_dir:
            directives.append(f"  LOW {field_name} ({value:.2f}): {low_dir}")

    if not directives:
        return (
            "\n<ledger_interpretation>\n"
            "  Temperament traits are near baseline. "
            "React with neutral emotional impulses.\n"
            "</ledger_interpretation>"
        )

    header = (
        "Your innate temperament drives your emotional reactions. "
        "Express these impulses simply:"
    )
    return (
        "\n<ledger_interpretation>\n"
        f"  {header}\n"
        + "\n".join(directives)
        + "\n</ledger_interpretation>"
    )


def _build_ledger_interpretation(state: PersonalityState) -> str:
    """Translate salient personality scores into behavioral directives.

    The Personality Ledger is just a set of numbers.  The LLM is the
    only component capable of reading those numbers and manifesting them
    as specific behavioral changes (adjective choice, emotional tone,
    empathy level, etc.).  This function bridges the gap by identifying
    traits that deviate significantly from their baseline and generating
    explicit behavioral instructions the LLM must follow.

    Only salient traits (deviation > threshold from baseline) are included
    to keep the prompt focused and avoid information overload.
    """
    # Models with 0.5 baseline (HEXACO, TCI-Temperament)
    mid_baseline_models = [
        ("hexaco", state.hexaco, 0.5),
        ("tci_temperament", state.tci_temperament, 0.5),
    ]
    # Models with 0.0 baseline (TCI-Character, Schwartz)
    zero_baseline_models = [
        ("tci_character", state.tci_character, 0.0),
        ("schwartz", state.schwartz, 0.0),
    ]

    directives: list[str] = []

    for _model_name, model, baseline in mid_baseline_models + zero_baseline_models:
        for field_name in type(model).model_fields:
            value = getattr(model, field_name)
            deviation = value - baseline

            if field_name not in _FACET_DIRECTIVES:
                continue

            high_dir, low_dir = _FACET_DIRECTIVES[field_name]

            if baseline == 0.0:
                if value >= _ZERO_BASELINE_THRESHOLD and high_dir:
                    directives.append(f"  {field_name}={value:.2f}: {high_dir}")
            elif deviation > _SALIENCE_THRESHOLD and high_dir:
                directives.append(f"  HIGH {field_name} ({value:.2f}): {high_dir}")
            elif deviation < -_SALIENCE_THRESHOLD and low_dir:
                directives.append(f"  LOW {field_name} ({value:.2f}): {low_dir}")

    if not directives:
        return (
            "\n<ledger_interpretation>\n"
            "  All personality traits are near baseline. "
            "Behave neutrally until traits evolve through interaction.\n"
            "</ledger_interpretation>"
        )

    header = (
        "Your Personality Ledger encodes WHO you are. "
        "These scores MUST drive your tone, word choice, and emotional expression:"
    )
    return (
        "\n<ledger_interpretation>\n"
        f"  {header}\n"
        + "\n".join(directives)
        + "\n</ledger_interpretation>"
    )
