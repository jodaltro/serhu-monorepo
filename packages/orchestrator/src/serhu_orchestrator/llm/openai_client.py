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
VALID_CHAT_ROLES = {"system", "assistant", "user", "function", "tool", "developer"}


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
            role = self._normalize_role(m.get("role", "user"))
            api_messages.append({
                "role": role,
                "content": m.get("content", ""),
            })

        response = self._client.chat.completions.create(
            model=self._model,
            messages=api_messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
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

    @staticmethod
    def _normalize_role(role: str) -> str:
        """Normalize internal roles to OpenAI Chat API compatible roles."""
        role_map = {
            "being": "assistant",
            "assistant": "assistant",
            "user": "user",
            "system": "system",
            "developer": "developer",
            "tool": "tool",
            "function": "function",
        }
        normalized = role_map.get((role or "").strip().lower(), "user")
        if normalized in VALID_CHAT_ROLES:
            return normalized
        return "user"

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
            max_completion_tokens=512,
        )

        raw = response.choices[0].message.content or "{}"
        return self._parse_trait_deltas(raw)

    # -- LLMClient.extract_semantic_facts -----------------------------------

    def extract_semantic_facts(
        self,
        episodes: list[dict],
        personality_summary: str,
    ) -> list[str]:
        """LLM-powered episodic → semantic memory transformation.

        Acts as a 'memory manager' that reads conversation logs and
        transforms them into distilled semantic knowledge: recurring
        themes, emotional patterns, user beliefs, and relational facts.
        """
        episode_texts = []
        for ep in episodes[-30:]:
            role = ep.get("role", "unknown")
            content = ep.get("content", "")
            episode_texts.append(f"[{role}] {content}")

        episodes_block = "\n".join(episode_texts)

        extraction_prompt = (
            "You are the MEMORY MANAGER for a synthetic Being.\n"
            "Your task: transform raw episodic memory (conversation logs) into "
            "semantic memory (distilled facts, beliefs, and patterns).\n\n"
            "Analyse the episodes and extract:\n"
            "1. Recurring themes the user returns to.\n"
            "2. Emotional patterns (e.g., 'the user feels tired after work').\n"
            "3. User preferences and values.\n"
            "4. Relationship dynamics between user and Being.\n"
            "5. Inferred beliefs about the user's world.\n\n"
            "Rules:\n"
            "- Extract 3-7 concise factual statements.\n"
            "- Each fact should be a single, actionable sentence.\n"
            "- Focus on PATTERNS, not individual events.\n"
            "- Return ONLY a JSON array of strings.\n\n"
            f"Being personality summary:\n{personality_summary}\n\n"
            f"Recent episodes:\n{episodes_block}\n\n"
            "Return the semantic facts as a JSON array:"
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.3,
            max_completion_tokens=512,
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
            max_completion_tokens=256,
        )

        raw = response.choices[0].message.content or "[]"
        return self._parse_string_list(raw)

    # -- LLMClient.generate_dream_hypotheses --------------------------------

    def generate_dream_hypotheses(
        self,
        episodes: list[dict],
        personality_summary: str,
        num_hypotheses: int = 10,
    ) -> list[str]:
        """Generate dream hypotheses via Solomonoff Induction.

        The LLM identifies algorithmic patterns in the observed episodic
        data and produces concise explanations/predictions.  This replaces
        the random hypothesis generation with meaningful pattern discovery.
        """
        episode_texts = []
        for ep in episodes[-20:]:
            role = ep.get("role", "unknown")
            content = ep.get("content", "")
            episode_texts.append(f"[{role}] {content}")

        episodes_block = "\n".join(episode_texts)

        hypothesis_prompt = (
            "You are a SOLOMONOFF INDUCTION engine for a synthetic Being's dream cycle.\n"
            "Your task: discover algorithmic patterns in the observed data and generate\n"
            "concise hypotheses that explain the user's behavior and the world.\n\n"
            "A hypothesis is a SIMPLE explanatory pattern, like:\n"
            "- 'The user seeks emotional validation when discussing work'\n"
            "- 'Topics about nature trigger positive emotional states'\n"
            "- 'The user values honesty over comfort'\n\n"
            "Prefer SIMPLER hypotheses (Occam's razor / Kolmogorov complexity).\n\n"
            "Rules:\n"
            f"- Generate exactly {num_hypotheses} hypotheses.\n"
            "- Each hypothesis should be a single concise sentence.\n"
            "- Focus on patterns, not individual events.\n"
            "- Return ONLY a JSON array of strings.\n\n"
            f"Being personality summary:\n{personality_summary}\n\n"
            f"Observed episodes:\n{episodes_block}\n\n"
            "Return the hypotheses as a JSON array:"
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": hypothesis_prompt}],
            temperature=0.5,
            max_completion_tokens=512,
        )

        raw = response.choices[0].message.content or "[]"
        return self._parse_string_list(raw)

    # -- LLMClient.simulate_dream_rollouts ----------------------------------

    def simulate_dream_rollouts(
        self,
        hypotheses: list[str],
        personality_summary: str,
        recent_context: list[str],
    ) -> list[dict]:
        """Simulate future conversations to test personality coherence.

        The LLM projects how the Being would react to each hypothesis,
        scoring each for coherence with the consolidated personality.
        Returns scored simulations as dicts with action, reward, complexity.
        """
        hypotheses_block = "\n".join(f"- {h}" for h in hypotheses[:10])
        context_block = "\n".join(recent_context[-5:])

        simulation_prompt = (
            "You are the DREAM SIMULATOR for a synthetic Being.\n"
            "For each hypothesis, simulate how the Being would react in a future\n"
            "conversation.  Score each for coherence with the personality.\n\n"
            "For each hypothesis, return:\n"
            "- 'action': a brief description of the Being's simulated reaction\n"
            "- 'reward': coherence score from 0.0 (incoherent) to 1.0 (perfect fit)\n"
            "- 'complexity': Kolmogorov-like complexity from 0.0 (simple) to 1.0 (complex)\n\n"
            "Rules:\n"
            "- Prefer simple hypotheses with high coherence (Occam's razor).\n"
            "- Return ONLY a JSON array of objects.\n\n"
            f"Being personality summary:\n{personality_summary}\n\n"
            f"Recent context:\n{context_block}\n\n"
            f"Hypotheses to simulate:\n{hypotheses_block}\n\n"
            "Return the scored simulations as a JSON array:"
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": simulation_prompt}],
            temperature=0.3,
            max_completion_tokens=1024,
        )

        raw = response.choices[0].message.content or "[]"
        return self._parse_rollout_results(raw)

    # -- LLMClient.extract_environment_spec ---------------------------------

    def extract_environment_spec(
        self,
        episodes: list[dict],
        personality_summary: str,
    ) -> dict:
        """Extract AIXI environment inputs from episodes and personality.

        Called once at the start of sleep.  Returns a structured dict
        that ``EnvironmentBuilder._parse_llm_spec()`` converts into an
        ``EnvironmentSpec``.
        """
        episode_texts = []
        for ep in episodes[-30:]:
            role = ep.get("role", "unknown")
            content = ep.get("content", "")
            episode_texts.append(f"[{role}] {content}")

        episodes_block = "\n".join(episode_texts)

        extraction_prompt = (
            "You are an ENVIRONMENT DESIGNER for a synthetic Being's AIXI dream cycle.\n"
            "Analyze the Being's personality and interaction history to design a "
            "reinforcement learning environment for dream simulation.\n\n"
            "From the episodes and personality, extract:\n"
            "1. **actions**: A list of 8-15 specific actions the Being can take "
            "(e.g. 'explore_nature', 'ask_about_feelings', 'discuss_music').\n"
            "2. **observations**: A list of 6-12 possible observations/states "
            "(e.g. 'user_happy', 'user_curious', 'topic_nature').\n"
            "3. **reward_signals**: A dict mapping action/observation patterns to "
            "reward values (-1.0 to 1.0) based on what's good for this Being.\n"
            "4. **transition_weights**: For each action, a list of "
            "[observation, probability] pairs showing likely outcomes "
            "(parsed into a separate WorldModel by the system).\n"
            "5. **horizon**: How many steps ahead to simulate (5-20).\n"
            "6. **gamma**: Temporal discount factor (0.8-0.99).\n\n"
            "Rules:\n"
            "- Actions should reflect the Being's learned topics and capabilities.\n"
            "- Observations should reflect the user's typical states and reactions.\n"
            "- Rewards should align with the Being's personality and values.\n"
            "- Return ONLY valid JSON.\n\n"
            f"Being personality summary:\n{personality_summary}\n\n"
            f"Recent episodes:\n{episodes_block}\n\n"
            "Return the environment specification as JSON:"
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.3,
            max_completion_tokens=1024,
        )

        raw = response.choices[0].message.content or "{}"
        return self._parse_environment_spec(raw)

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _strip_code_fence(raw: str) -> str:
        """Remove markdown code fences from LLM output."""
        import re
        cleaned = raw.strip()
        # Handle ```json\n...\n``` and ```\n...\n``` and ```json[...]```
        match = re.match(r"^```(?:json)?\s*\n?(.*?)```\s*$", cleaned, re.DOTALL)
        if match:
            return match.group(1).strip()
        return cleaned

    @staticmethod
    def _clamp_score(
        value: float, min_val: float = 0.0, max_val: float = 1.0
    ) -> float:
        """Clamp a numeric score to the given bounds."""
        return max(min_val, min(max_val, float(value)))

    @staticmethod
    def _parse_trait_deltas(raw: str) -> dict[str, dict[str, float]]:
        """Parse trait deltas from LLM JSON output with graceful fallback."""
        try:
            cleaned = OpenAIClient._strip_code_fence(raw)
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
                        clamped = OpenAIClient._clamp_score(
                            value, min_val=-0.05, max_val=0.05
                        )
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
            cleaned = OpenAIClient._strip_code_fence(raw)
            data = json.loads(cleaned)
            if isinstance(data, list):
                return [str(item) for item in data if item]
            return []
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse string list from LLM response: %s", raw[:200])
            return []

    @staticmethod
    def _parse_rollout_results(raw: str) -> list[dict]:
        """Parse dream rollout results from LLM JSON output."""
        try:
            cleaned = OpenAIClient._strip_code_fence(raw)
            data = json.loads(cleaned)
            if not isinstance(data, list):
                return []
            results: list[dict] = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                action = str(item.get("action", ""))
                reward = OpenAIClient._clamp_score(
                    float(item.get("reward", 0.0))
                )
                complexity = OpenAIClient._clamp_score(
                    float(item.get("complexity", 0.0))
                )
                if action:
                    results.append({
                        "action": action,
                        "reward": reward,
                        "complexity": complexity,
                    })
            return results
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning(
                "Failed to parse rollout results from LLM response: %s", raw[:200]
            )
            return []

    @staticmethod
    def _parse_environment_spec(raw: str) -> dict:
        """Parse environment specification from LLM JSON output."""
        try:
            cleaned = OpenAIClient._strip_code_fence(raw)
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
            return {}
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "Failed to parse environment spec from LLM response: %s",
                raw[:200],
            )
            return {}
