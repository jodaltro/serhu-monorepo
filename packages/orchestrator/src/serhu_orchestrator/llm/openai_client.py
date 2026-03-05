"""OpenAI GPT-5.4 client – concrete LLM implementation.

Provides the ``OpenAIClient`` class that wraps the OpenAI Python SDK
to satisfy the ``LLMClient`` protocol.  Used by the Orchestrator for:
1. **Wakefulness** – Generating Being responses and extracting trait deltas.
2. **Sleep**       – LLM-powered semantization and belief derivation.

References:
    - OpenAI Chat API: https://platform.openai.com/docs/api-reference/chat
    - GPT-5.4: https://openai.com/index/introducing-gpt-5/
    - Persona vectors: https://www.anthropic.com/research/persona-vectors
"""

from __future__ import annotations

import json
import logging

from openai import OpenAI

from serhu_orchestrator.llm.llm_client import LLMResponse

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-5.4"


class OpenAIClient:
    """GPT-5.4 client satisfying the ``LLMClient`` protocol.

    Parameters
    ----------
    api_key : str
        OpenAI API key.
    model : str
        Model identifier (default: ``gpt-5.4``).
    """

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    # -- LLMClient.chat ------------------------------------------------------

    def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a conversational response via GPT-5.4.

        Combines the structured system prompt (with HEXACO/TCI/Schwartz
        scores and Piaget constraints) with the conversation history.
        """
        api_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            api_messages.append({
                "role": m.get("role", "user"),
                "content": m.get("content", ""),
            })

        response = self._client.chat.completions.create(
            model=self._model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=usage,
        )

    # -- LLMClient.analyze_traits -------------------------------------------

    def analyze_traits(
        self,
        system_prompt: str,
        conversation_turn: str,
        being_response: str,
    ) -> dict[str, dict[str, float]]:
        """Extract personality trait deltas via GPT-5.4.

        Asks the model to act as a psychometric classifier, analysing the
        conversation turn and returning structured HEXACO/TCI/Schwartz deltas.
        """
        analysis_prompt = (
            "You are a psychometric analysis engine for a synthetic Being.\n"
            "Given the Being's current personality profile and a conversation turn,\n"
            "determine how the Being's personality traits should shift.\n\n"
            "Rules:\n"
            "- Return ONLY valid JSON with nested dicts.\n"
            "- Top-level keys: hexaco, tci_temperament, tci_character, schwartz.\n"
            "- Values are small float deltas between -0.05 and +0.05.\n"
            "- Only include traits that should change.\n"
            "- If no traits should change, return {}.\n\n"
            f"Current personality context:\n{system_prompt}\n\n"
            f"User said: {conversation_turn}\n"
            f"Being responded: {being_response}\n\n"
            "Return the trait deltas as JSON:"
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.2,
            max_tokens=512,
        )

        raw = response.choices[0].message.content or "{}"
        return self._parse_trait_deltas(raw)

    # -- LLMClient.extract_semantic_facts -----------------------------------

    def extract_semantic_facts(
        self,
        episodes: list[dict],
        personality_summary: str,
    ) -> list[str]:
        """LLM-powered fact extraction during sleep semantization.

        Analyses recent episodes to identify recurring themes, emotional
        patterns, and factual knowledge the Being should remember.
        """
        episode_texts = []
        for ep in episodes[-30:]:
            role = ep.get("role", "unknown")
            content = ep.get("content", "")
            episode_texts.append(f"[{role}] {content}")

        episodes_block = "\n".join(episode_texts)

        extraction_prompt = (
            "You are the memory consolidation engine for a synthetic Being.\n"
            "Analyze the recent conversation episodes and extract semantic facts.\n\n"
            "Rules:\n"
            "- Extract 3-7 concise factual statements.\n"
            "- Focus on recurring themes, user preferences, and emotional patterns.\n"
            "- Each fact should be a single sentence.\n"
            "- Return ONLY a JSON array of strings.\n\n"
            f"Being personality summary:\n{personality_summary}\n\n"
            f"Recent episodes:\n{episodes_block}\n\n"
            "Return the facts as a JSON array:"
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.3,
            max_tokens=512,
        )

        raw = response.choices[0].message.content or "[]"
        return self._parse_string_list(raw)

    # -- LLMClient.derive_beliefs -------------------------------------------

    def derive_beliefs(
        self,
        hypotheses: list[str],
        personality_summary: str,
    ) -> list[str]:
        """LLM-powered belief derivation during sleep.

        Implements the Jungian reflection mechanism: the LLM acts as the
        'Observer' analysing dream hypotheses to derive core beliefs.

        Reference: https://arxiv.org/html/2601.10025v1
        """
        hypotheses_block = "\n".join(f"- {h}" for h in hypotheses[:10])

        derivation_prompt = (
            "You are the Jungian Observer for a synthetic Being's dream cycle.\n"
            "Analyze the dream hypotheses and derive core beliefs.\n\n"
            "Rules:\n"
            "- Derive 1-3 core beliefs from the patterns.\n"
            "- Beliefs should be concise statements about self, world, or relationships.\n"
            "- Consider the Being's personality when filtering relevant patterns.\n"
            "- Return ONLY a JSON array of strings.\n\n"
            f"Being personality summary:\n{personality_summary}\n\n"
            f"Dream hypotheses:\n{hypotheses_block}\n\n"
            "Return the beliefs as a JSON array:"
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": derivation_prompt}],
            temperature=0.4,
            max_tokens=256,
        )

        raw = response.choices[0].message.content or "[]"
        return self._parse_string_list(raw)

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _parse_trait_deltas(raw: str) -> dict[str, dict[str, float]]:
        """Parse trait deltas from LLM JSON output with graceful fallback."""
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(cleaned)
            if not isinstance(data, dict):
                return {}
            result: dict[str, dict[str, float]] = {}
            valid_models = {"hexaco", "tci_temperament", "tci_character", "schwartz"}
            for model_key, traits in data.items():
                if model_key not in valid_models or not isinstance(traits, dict):
                    continue
                parsed_traits: dict[str, float] = {}
                for trait_name, value in traits.items():
                    if isinstance(value, (int, float)):
                        clamped = max(-0.05, min(0.05, float(value)))
                        parsed_traits[trait_name] = clamped
                if parsed_traits:
                    result[model_key] = parsed_traits
            return result
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse trait deltas from LLM response: %s", raw[:200])
            return {}

    @staticmethod
    def _parse_string_list(raw: str) -> list[str]:
        """Parse a JSON string list from LLM output with graceful fallback."""
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(cleaned)
            if isinstance(data, list):
                return [str(item) for item in data if item]
            return []
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse string list from LLM response: %s", raw[:200])
            return []
