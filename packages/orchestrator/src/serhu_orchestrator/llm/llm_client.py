"""Abstract LLM client protocol.

Defines the contract that any LLM provider must satisfy so the
Orchestrator can generate Being responses, extract personality traits,
and enhance sleep-cycle semantization.

Using ``Protocol`` instead of ABC allows structural subtyping:
any class with matching methods is accepted without explicit inheritance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class LLMResponse:
    """Standard response from an LLM call.

    Attributes
    ----------
    content : str
        The generated text.
    model : str
        Model identifier that produced the response.
    usage : dict
        Token usage breakdown (prompt_tokens, completion_tokens, total_tokens).
    """

    content: str
    model: str = ""
    usage: dict = field(default_factory=dict)


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM providers used by the Orchestrator.

    Any class implementing these three methods can be used as the LLM
    backend for a synthetic Being.
    """

    def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a conversational response.

        Parameters
        ----------
        system_prompt : str
            The system prompt (built by ``build_system_prompt``).
        messages : list[dict[str, str]]
            Conversation history as ``[{"role": ..., "content": ...}, ...]``.
        temperature : float
            Sampling temperature.
        max_tokens : int
            Maximum tokens in the response.
        """
        ...

    def analyze_traits(
        self,
        system_prompt: str,
        conversation_turn: str,
        being_response: str,
    ) -> dict[str, dict[str, float]]:
        """Extract personality trait deltas from a conversation turn.

        Uses the LLM as a psychometric classifier to determine how the
        latest interaction should shift the Being's HEXACO, TCI-R, and
        Schwartz scores.

        Parameters
        ----------
        system_prompt : str
            Current personality context.
        conversation_turn : str
            The user's message.
        being_response : str
            The Being's response.

        Returns
        -------
        dict[str, dict[str, float]]
            Nested deltas, e.g. ``{"hexaco": {"sincerity": 0.02}, ...}``.
        """
        ...

    def extract_semantic_facts(
        self,
        episodes: list[dict],
        personality_summary: str,
    ) -> list[str]:
        """Extract semantic facts from episodic memory during sleep.

        Replaces the rule-based ``_semantize()`` with LLM-powered
        analysis of recurring patterns, themes, and insights.

        Parameters
        ----------
        episodes : list[dict]
            Recent episodic memory entries.
        personality_summary : str
            Summary of the Being's current personality state.

        Returns
        -------
        list[str]
            Distilled semantic facts.
        """
        ...

    def derive_beliefs(
        self,
        hypotheses: list[str],
        personality_summary: str,
    ) -> list[str]:
        """Derive core beliefs from dream hypotheses during sleep.

        Enhances the Jungian reflection mechanism by using the LLM
        to evaluate which dream patterns should become permanent beliefs.

        Parameters
        ----------
        hypotheses : list[str]
            Top dream hypotheses from AIXI rollouts.
        personality_summary : str
            Summary of the Being's current personality state.

        Returns
        -------
        list[str]
            New core beliefs to add to the Being's belief stack.
        """
        ...

    def generate_dream_hypotheses(
        self,
        episodes: list[dict],
        personality_summary: str,
        num_hypotheses: int = 10,
    ) -> list[str]:
        """Generate dream hypotheses via Solomonoff Induction.

        The LLM acts as a universal solver, identifying algorithmic
        patterns in the observed episodic data and generating concise
        explanations/predictions about the user and the world.

        Parameters
        ----------
        episodes : list[dict]
            Recent episodic memory entries.
        personality_summary : str
            Summary of the Being's current personality state.
        num_hypotheses : int
            Number of hypotheses to generate.

        Returns
        -------
        list[str]
            Generated hypothesis strings.
        """
        ...

    def simulate_dream_rollouts(
        self,
        hypotheses: list[str],
        personality_summary: str,
        recent_context: list[str],
    ) -> list[dict]:
        """Simulate future conversations to test personality coherence.

        The LLM projects how the Being would react to each hypothesis,
        scoring each for coherence with the consolidated personality.

        Parameters
        ----------
        hypotheses : list[str]
            Hypotheses to simulate.
        personality_summary : str
            Summary of the Being's current personality state.
        recent_context : list[str]
            Recent conversation content for context grounding.

        Returns
        -------
        list[dict]
            List of ``{"action": str, "reward": float, "complexity": float}``.
        """
        ...

    def extract_environment_spec(
        self,
        episodes: list[dict],
        personality_summary: str,
    ) -> dict:
        """Extract AIXI environment inputs at the start of sleep.

        Called **once** at the beginning of the sleep cycle to produce
        the environment specification that the AIXI rollouts will use.
        This is the only LLM call during sleep.

        The returned dict should contain:
        - ``actions``: list of action strings the Being can take.
        - ``observations``: list of observation strings.
        - ``reward_signals``: dict mapping patterns to reward values.
        - ``transition_weights``: dict mapping actions to
          ``[(observation, probability)]`` lists.
        - ``horizon``: int, maximum look-ahead steps.
        - ``gamma``: float, discount factor.

        Parameters
        ----------
        episodes : list[dict]
            Recent episodic memory entries.
        personality_summary : str
            Summary of the Being's current personality state.

        Returns
        -------
        dict
            Raw environment specification for ``EnvironmentBuilder._parse_llm_spec()``.
        """
        ...
