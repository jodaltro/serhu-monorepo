"""Human World Envelope – ontology of everyday domains.

Defines 6 plausible everyday domains that constrain all generated
curriculum content, keeping the Being's initial world model grounded
in common human experience.

Each domain includes stage-specific vocabulary and concepts that scale
with cognitive development.

References:
    - Piaget stages: https://www.simplypsychology.org/piaget.html
    - Zone of Proximal Development (Vygotsky):
      https://en.wikipedia.org/wiki/Zone_of_proximal_development
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Domain:
    """A single domain in the Human World Envelope.

    Parameters
    ----------
    name : str
        Machine-readable domain identifier.
    label : str
        Human-readable domain name.
    description : str
        Short description of the domain scope.
    stage_vocabulary : dict[str, list[str]]
        Per-stage vocabulary (words/concepts the Being can encounter).
    """

    name: str
    label: str
    description: str
    stage_vocabulary: dict[str, list[str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# The 6 core domains
# ---------------------------------------------------------------------------

EVERYDAY_OBJECTS = Domain(
    name="everyday_objects",
    label="Everyday Objects",
    description="Common household objects, food, toys, and their properties.",
    stage_vocabulary={
        "sensorimotor": [
            "ball", "cup", "spoon", "bottle", "blanket", "toy", "block",
            "rattle", "teddy", "shoe", "plate", "water", "milk", "bread",
            "apple", "banana", "chair", "table", "door", "light",
        ],
        "preoperational": [
            "ball", "cup", "spoon", "car", "doll", "crayon", "book",
            "pillow", "soap", "brush", "clock", "mirror", "key", "bag",
            "hat", "coat", "phone", "flower", "leaf", "stone",
            "red", "blue", "green", "yellow", "big", "small",
            "round", "soft", "hard", "warm", "cold",
        ],
        "concrete_operational": [
            "tool", "instrument", "device", "container", "material",
            "wood", "metal", "plastic", "glass", "fabric",
            "measure", "weight", "length", "temperature",
            "recipe", "ingredient", "product", "machine",
        ],
        "formal_operational": [
            "mechanism", "system", "structure", "property",
            "composition", "function", "design", "invention",
            "resource", "sustainability", "technology",
        ],
    },
)

SPACE_TIME = Domain(
    name="space_time",
    label="Space and Time",
    description="Spatial relations, temporal sequences, and navigation.",
    stage_vocabulary={
        "sensorimotor": [
            "here", "there", "up", "down", "in", "out", "near", "far",
            "gone", "back", "now", "again", "more", "stop",
        ],
        "preoperational": [
            "near", "far", "inside", "outside", "above", "below",
            "before", "after", "morning", "night", "today", "tomorrow",
            "yesterday", "fast", "slow", "first", "last", "next",
            "left", "right", "front", "behind",
        ],
        "concrete_operational": [
            "distance", "direction", "position", "speed", "duration",
            "sequence", "order", "schedule", "calendar", "season",
            "hour", "minute", "week", "month", "year",
            "north", "south", "east", "west", "map",
        ],
        "formal_operational": [
            "dimension", "perspective", "relativity", "simultaneity",
            "causality", "timeline", "prediction", "planning",
            "probability", "frequency", "cycle", "pattern",
        ],
    },
)

PHYSICAL_ACTIONS = Domain(
    name="physical_actions",
    label="Physical Actions",
    description="Body movements, object manipulation, and physical causality.",
    stage_vocabulary={
        "sensorimotor": [
            "grab", "drop", "push", "pull", "shake", "hit", "throw",
            "fall", "roll", "open", "close", "eat", "drink",
            "cry", "laugh", "sleep", "look", "touch", "hear",
        ],
        "preoperational": [
            "pick up", "put down", "carry", "pour", "mix", "cut",
            "draw", "paint", "build", "break", "fix", "run", "jump",
            "climb", "swim", "ride", "kick", "catch", "hide", "find",
        ],
        "concrete_operational": [
            "assemble", "measure", "weigh", "compare", "sort",
            "organize", "arrange", "transform", "combine", "separate",
            "balance", "tilt", "rotate", "stretch", "compress",
        ],
        "formal_operational": [
            "engineer", "construct", "optimize", "calibrate",
            "experiment", "hypothesize", "test", "verify",
            "simulate", "model", "iterate", "refine",
        ],
    },
)

SOCIAL_ROUTINES = Domain(
    name="social_routines",
    label="Social Routines",
    description="Greetings, requests, emotions, and basic social interactions.",
    stage_vocabulary={
        "sensorimotor": [
            "mama", "papa", "hello", "bye", "yes", "no", "want",
            "mine", "hug", "kiss", "smile", "wave", "peek",
        ],
        "preoperational": [
            "hello", "goodbye", "please", "thank you", "sorry",
            "friend", "family", "share", "take turns", "help",
            "happy", "sad", "angry", "scared", "surprised",
            "love", "like", "want", "need", "name",
        ],
        "concrete_operational": [
            "cooperate", "negotiate", "apologize", "forgive",
            "agree", "disagree", "explain", "convince", "promise",
            "rule", "fair", "unfair", "responsibility", "trust",
            "team", "group", "role", "leader",
        ],
        "formal_operational": [
            "empathy", "perspective", "compromise", "conflict",
            "ethics", "justice", "rights", "obligation", "consent",
            "culture", "tradition", "identity", "community",
            "communication", "relationship", "boundary",
        ],
    },
)

TASKS_AND_RULES = Domain(
    name="tasks_and_rules",
    label="Tasks and Rules",
    description="Ordering, counting, classification, and rule-following.",
    stage_vocabulary={
        "sensorimotor": [
            "one", "two", "more", "all gone", "same", "different",
            "again", "done", "give", "take",
        ],
        "preoperational": [
            "count", "number", "color", "shape", "size", "group",
            "match", "same", "different", "sort", "category",
            "first", "second", "third", "pattern", "repeat",
        ],
        "concrete_operational": [
            "classify", "order", "sequence", "rank", "compare",
            "add", "subtract", "multiply", "divide", "equal",
            "greater", "less", "rule", "exception", "condition",
            "step", "instruction", "procedure", "result",
        ],
        "formal_operational": [
            "algorithm", "strategy", "analysis", "synthesis",
            "hypothesis", "variable", "control", "outcome",
            "logic", "deduction", "induction", "abstraction",
            "generalize", "specialize", "criteria", "evaluation",
        ],
    },
)

COMMUNICATION = Domain(
    name="communication",
    label="Communication",
    description="Questions, answers, corrections, and meta-communication.",
    stage_vocabulary={
        "sensorimotor": [
            "what", "this", "that", "look", "listen", "sound",
            "word", "name", "say", "sing",
        ],
        "preoperational": [
            "why", "what", "how", "who", "where", "when",
            "tell", "ask", "answer", "story", "describe",
            "true", "false", "pretend", "imagine", "remember",
        ],
        "concrete_operational": [
            "explain", "describe", "define", "summarize",
            "compare", "contrast", "example", "evidence",
            "reason", "because", "therefore", "however",
            "clarify", "correct", "confirm", "question",
        ],
        "formal_operational": [
            "argue", "debate", "persuade", "analyze",
            "interpret", "evaluate", "critique", "reflect",
            "metaphor", "analogy", "irony", "nuance",
            "implication", "assumption", "conclusion",
        ],
    },
)

# ---------------------------------------------------------------------------
# Assembled envelope
# ---------------------------------------------------------------------------

ALL_DOMAINS: list[Domain] = [
    EVERYDAY_OBJECTS,
    SPACE_TIME,
    PHYSICAL_ACTIONS,
    SOCIAL_ROUTINES,
    TASKS_AND_RULES,
    COMMUNICATION,
]

HUMAN_WORLD_ENVELOPE = {d.name: d for d in ALL_DOMAINS}


def get_domain_names() -> list[str]:
    """Return the list of all domain names."""
    return [d.name for d in ALL_DOMAINS]


def get_stage_vocabulary(domain_name: str, stage: str) -> list[str]:
    """Return vocabulary for a domain at a given Piaget stage.

    Falls back to an empty list if the domain or stage is unknown.
    """
    domain = HUMAN_WORLD_ENVELOPE.get(domain_name)
    if domain is None:
        return []
    return list(domain.stage_vocabulary.get(stage, []))


def get_all_stage_vocabulary(stage: str) -> dict[str, list[str]]:
    """Return vocabulary for all domains at a given Piaget stage."""
    return {
        d.name: list(d.stage_vocabulary.get(stage, []))
        for d in ALL_DOMAINS
    }
