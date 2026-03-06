"""Neural Engine – Transformer-inspired self-learning for the Being's sleep.

Implements a lightweight internal "language model" that the Being builds
from its own episodic memories during sleep cycles.  Instead of relying
on an external LLM (GPT-5.4), the Being learns through:

1. **Vocabulary Construction** – TF-IDF weighted token extraction from episodes.
2. **Self-Attention Pattern Discovery** – Dot-product attention over episode
   embeddings to find semantically related clusters of experience.
3. **N-gram Pattern Mining** – Bigram/trigram frequency analysis for
   identifying recurring conversational patterns.
4. **Personality-Weighted Coherence** – Attention scores modulated by the
   Being's personality vector to prefer patterns aligned with its identity.
5. **Generative Composition** – Response generation by combining learned
   patterns weighted by attention and personality.

This is the Being's *own* generative model, built entirely from its
interactions—no external API calls required.

References:
    - Attention Is All You Need: https://arxiv.org/abs/1706.03762
    - TF-IDF: https://en.wikipedia.org/wiki/Tf%E2%80%93idf
    - Self-supervised learning: https://arxiv.org/abs/2006.08218
    - AIXI: https://www.alignmentforum.org/w/aixi
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LearnedPattern:
    """A pattern discovered during self-attention over episodes.

    Attributes
    ----------
    tokens : list[str]
        The token sequence forming this pattern.
    weight : float
        Attention-weighted importance score.
    frequency : int
        Number of times this pattern appears in episodes.
    source_episodes : list[int]
        Indices of episodes where this pattern was observed.
    """

    tokens: list[str]
    weight: float = 0.0
    frequency: int = 1
    source_episodes: list[int] = field(default_factory=list)


@dataclass
class TrainingResult:
    """Result of a neural engine training cycle.

    Attributes
    ----------
    vocabulary_size : int
        Number of unique tokens learned.
    pattern_count : int
        Number of distinct patterns discovered.
    attention_entropy : float
        Shannon entropy of the attention distribution.
        Low entropy = focused learning; high = diffuse.
    top_patterns : list[str]
        Human-readable descriptions of top discovered patterns.
    """

    vocabulary_size: int = 0
    pattern_count: int = 0
    attention_entropy: float = 0.0
    top_patterns: list[str] = field(default_factory=list)


# Stop words for filtering (minimal set, covers EN, PT, ES, FR)
_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "must", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "or", "and", "but",
    "not", "no", "if", "so", "it", "its", "this", "that", "i", "me",
    "you", "he", "she", "we", "they", "my", "your", "his", "her", "our",
    "their", "what", "which", "who", "when", "where", "how", "all",
    # Portuguese common stop words
    "o", "os", "um", "uma", "de", "da", "do", "das", "dos", "em", "na",
    "no", "nas", "nos", "por", "para", "com", "se", "eu", "ele", "ela",
    "que", "é", "são", "foi", "ser", "ter", "como", "mais", "mas",
    # Spanish
    "el", "la", "los", "las", "es", "son", "del", "al", "y", "en",
    # French
    "le", "les", "un", "une", "des", "du", "est", "et", "en", "au",
})

# Minimum token length to consider meaningful
_MIN_TOKEN_LEN = 2

# Named indices into the 72-dim personality vector
# HEXACO (24): [0..23], TCI-T (16): [24..39], TCI-C (13): [40..52], Schwartz (19): [53..71]
_OPENNESS_INDEX = 20        # HEXACO Openness: aesthetic_appreciation
_CONSCIENTIOUSNESS_INDEX = 16  # HEXACO Conscientiousness: organization
_CURIOSITY_INDEX = 24        # TCI-T: exploratory_excitability (Novelty Seeking)

# Maximum number of n-grams to retain per type
_MAX_BIGRAMS = 500
_MAX_TRIGRAMS = 200
_MAX_UNIGRAMS = 100


class NeuralEngine:
    """Transformer-inspired self-learning engine.

    Builds an internal language model from episodic memories during sleep.
    Uses attention mechanisms and n-gram patterns to discover and generate
    knowledge without external LLM dependency.

    This engine is trained during the sleep cycle and produces:
    - Semantic facts from pattern clustering
    - Dream hypotheses from attention-weighted compositions
    - Belief candidates from high-confidence recurring patterns
    - Response fragments for the Being's self-generated speech

    Parameters
    ----------
    seed : int | None
        Random seed for reproducible results.
    """

    def __init__(self, seed: int | None = None) -> None:
        import random
        self._rng = random.Random(seed)

        # Learned state (built during train())
        self._vocabulary: dict[str, float] = {}  # token -> TF-IDF weight
        self._bigrams: dict[tuple[str, str], float] = {}  # bigram -> weight
        self._trigrams: dict[tuple[str, str, str], float] = {}  # trigram -> weight
        self._patterns: list[LearnedPattern] = []
        self._episode_vectors: list[list[float]] = []  # simplified embeddings
        self._attention_matrix: list[list[float]] = []  # episode-episode attention
        self._trained = False

    @property
    def is_trained(self) -> bool:
        """Whether the engine has been trained on episodes."""
        return self._trained

    @property
    def vocabulary_size(self) -> int:
        return len(self._vocabulary)

    @property
    def pattern_count(self) -> int:
        return len(self._patterns)

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into cleaned, filtered tokens (public API)."""
        return self._tokenize_text(text)

    def get_token_weight(self, token: str) -> float:
        """Get the TF-IDF weight of a token, or 0.0 if unknown."""
        return self._vocabulary.get(token.lower(), 0.0)

    def get_significant_tokens(
        self, tokens: list[str], threshold: float = 0.05
    ) -> list[tuple[str, float]]:
        """Return tokens with TF-IDF weight above the threshold."""
        return [
            (t, self._vocabulary.get(t, 0.0))
            for t in tokens
            if self._vocabulary.get(t, 0.0) > threshold
        ]

    # -- Training (the core sleep learning mechanism) -----------------------

    def train(
        self,
        episodes: list[dict],
        personality_vector: list[float],
    ) -> TrainingResult:
        """Train the internal model on episodic data.

        This is the main learning mechanism that runs during sleep.
        It implements a simplified transformer pipeline:

        1. Tokenize all episodes
        2. Build TF-IDF vocabulary
        3. Compute episode embeddings (bag-of-words + TF-IDF)
        4. Self-attention over episodes (scaled dot-product)
        5. Extract n-gram patterns
        6. Personality-weighted pattern scoring

        Parameters
        ----------
        episodes : list[dict]
            Episodic memory entries with 'content' and optionally 'role'.
        personality_vector : list[float]
            Flattened personality trait vector for weighting.

        Returns
        -------
        TrainingResult
            Metrics about what was learned.
        """
        if not episodes:
            return TrainingResult()

        # Phase 1: Tokenize
        episode_tokens = self._tokenize_episodes(episodes)

        # Phase 2: Build TF-IDF vocabulary
        self._build_vocabulary(episode_tokens)

        # Phase 3: Compute episode embeddings
        self._episode_vectors = self._compute_embeddings(episode_tokens)

        # Phase 4: Self-attention
        self._attention_matrix = self._compute_self_attention(
            self._episode_vectors, personality_vector
        )

        # Phase 5: N-gram pattern extraction
        self._extract_ngram_patterns(episode_tokens)

        # Phase 6: Personality-weighted pattern scoring
        self._score_patterns(personality_vector)

        self._trained = True

        entropy = self._compute_attention_entropy()
        top_patterns = [
            " ".join(p.tokens) for p in sorted(
                self._patterns, key=lambda p: p.weight, reverse=True
            )[:10]
        ]

        return TrainingResult(
            vocabulary_size=len(self._vocabulary),
            pattern_count=len(self._patterns),
            attention_entropy=entropy,
            top_patterns=top_patterns,
        )

    # -- Hypothesis Generation (replaces LLM-based generation) ---------------

    def generate_hypotheses(
        self,
        episodes: list[dict],
        personality_vector: list[float],
        num_hypotheses: int = 10,
    ) -> list[str]:
        """Generate hypotheses from learned patterns.

        Uses attention-weighted pattern composition to create hypotheses
        about the user's behavior and the world. Each hypothesis is a
        concise statement derived from the Being's learned patterns.

        Parameters
        ----------
        episodes : list[dict]
            Episodic data for context.
        personality_vector : list[float]
            Personality vector for weighting.
        num_hypotheses : int
            Number of hypotheses to generate.

        Returns
        -------
        list[str]
            Generated hypothesis strings.
        """
        if not self._trained:
            self.train(episodes, personality_vector)

        hypotheses: list[str] = []

        # Strategy 1: Top attention-weighted patterns → direct hypotheses
        sorted_patterns = sorted(
            self._patterns, key=lambda p: p.weight, reverse=True
        )
        for p in sorted_patterns[:num_hypotheses]:
            pattern_text = " ".join(p.tokens)
            if len(pattern_text) > 3:
                hypotheses.append(f"hypothesis_about:{pattern_text}")

        # Strategy 2: Cross-attention composition (combine high-attention episodes)
        if self._attention_matrix and len(hypotheses) < num_hypotheses:
            composed = self._compose_cross_attention_hypotheses(
                episodes, num_hypotheses - len(hypotheses)
            )
            hypotheses.extend(composed)

        # Strategy 3: Personality-modulated exploration
        if len(hypotheses) < num_hypotheses:
            explored = self._explore_novel_patterns(
                episodes, personality_vector, num_hypotheses - len(hypotheses)
            )
            hypotheses.extend(explored)

        return hypotheses[:num_hypotheses]

    # -- Semantic Fact Extraction (replaces LLM semantization) ---------------

    def extract_semantic_facts(
        self,
        episodes: list[dict],
        personality_vector: list[float],
    ) -> list[str]:
        """Extract semantic facts using learned patterns.

        Uses TF-IDF vocabulary and attention patterns to identify
        recurring themes and transform them into semantic facts.

        Parameters
        ----------
        episodes : list[dict]
            Episodic memory entries.
        personality_vector : list[float]
            Personality vector for context.

        Returns
        -------
        list[str]
            Extracted semantic fact strings.
        """
        if not self._trained:
            self.train(episodes, personality_vector)

        facts: list[str] = []

        # Fact type 1: High TF-IDF tokens → user frequently discusses topic
        top_tokens = sorted(
            self._vocabulary.items(), key=lambda x: x[1], reverse=True
        )[:15]
        for token, weight in top_tokens:
            if weight > 0.1 and len(token) > _MIN_TOKEN_LEN:
                facts.append(f"The user frequently mentions '{token}'")

        # Fact type 2: Recurring bigrams → behavioral patterns
        top_bigrams = sorted(
            self._bigrams.items(), key=lambda x: x[1], reverse=True
        )[:10]
        for (t1, t2), weight in top_bigrams:
            if weight > 0.05:
                facts.append(f"Pattern observed: '{t1} {t2}'")

        # Fact type 3: High attention clusters → semantically related themes
        if self._attention_matrix:
            clusters = self._find_attention_clusters(episodes)
            for cluster_desc in clusters[:5]:
                facts.append(cluster_desc)

        # Limit to reasonable number
        return facts[:10]

    # -- Belief Derivation (replaces LLM Jungian reflection) ----------------

    def derive_beliefs(
        self,
        hypotheses: list[str],
        personality_vector: list[float],
    ) -> list[str]:
        """Derive core beliefs from hypotheses using pattern analysis.

        Evaluates which hypotheses have the strongest support from
        the learned patterns and personality alignment.

        Parameters
        ----------
        hypotheses : list[str]
            Dream hypotheses to evaluate.
        personality_vector : list[float]
            Personality vector for alignment scoring.

        Returns
        -------
        list[str]
            Derived belief strings.
        """
        if not hypotheses:
            return []

        beliefs: list[str] = []

        # Score each hypothesis by vocabulary overlap and personality alignment
        scored: list[tuple[str, float]] = []
        for h in hypotheses[:10]:
            h_tokens = set(self._tokenize_text(h))
            # Vocabulary support: how many hypothesis tokens are in our vocabulary
            vocab_support = sum(
                self._vocabulary.get(t, 0.0) for t in h_tokens
            )
            # Pattern support: overlap with known patterns
            pattern_support = 0.0
            for p in self._patterns:
                overlap = len(h_tokens & set(p.tokens))
                if overlap > 0:
                    pattern_support += p.weight * overlap

            total_score = vocab_support + pattern_support
            scored.append((h, total_score))

        # Top scoring hypotheses become beliefs
        scored.sort(key=lambda x: x[1], reverse=True)
        for h_text, score in scored[:3]:
            if score > 0.0:
                beliefs.append(
                    f"Learned: {h_text} (confidence={min(score, 1.0):.2f})"
                )

        return beliefs

    # -- Response Generation (replaces external LLM chat) -------------------

    def generate_response(
        self,
        context: list[str],
        personality_vector: list[float],
        max_tokens: int = 50,
    ) -> str:
        """Generate a response from learned patterns.

        Composes a response by selecting and combining learned patterns
        that are most relevant to the current context, weighted by
        personality alignment.

        Parameters
        ----------
        context : list[str]
            Recent conversation context (last few messages).
        personality_vector : list[float]
            Personality vector for response shaping.
        max_tokens : int
            Maximum response length in tokens.

        Returns
        -------
        str
            Generated response text.
        """
        if not self._trained or not self._patterns:
            # Untrained: return a basic echo/mirror response
            if context:
                last = context[-1].split()
                if last:
                    return last[-1]
            return "..."

        # Find context-relevant patterns
        context_tokens = set()
        for msg in context[-5:]:
            context_tokens.update(self._tokenize_text(msg))

        # Score patterns by context relevance + personality alignment
        scored_patterns: list[tuple[LearnedPattern, float]] = []
        for p in self._patterns:
            overlap = len(context_tokens & set(p.tokens))
            relevance = overlap * p.weight
            scored_patterns.append((p, relevance))

        scored_patterns.sort(key=lambda x: x[1], reverse=True)

        # Compose response from top patterns
        response_tokens: list[str] = []
        used_patterns: set[int] = set()

        for p, score in scored_patterns:
            if score <= 0.0:
                continue
            pid = id(p)
            if pid in used_patterns:
                continue
            used_patterns.add(pid)

            for token in p.tokens:
                if len(response_tokens) >= max_tokens:
                    break
                response_tokens.append(token)

            if len(response_tokens) >= max_tokens:
                break

        if not response_tokens:
            # Fallback: use highest-weight pattern
            if scored_patterns:
                response_tokens = list(scored_patterns[0][0].tokens[:max_tokens])

        return " ".join(response_tokens[:max_tokens]) if response_tokens else "..."

    # -- Internal: Tokenization ---------------------------------------------

    @staticmethod
    def _tokenize_text(text: str) -> list[str]:
        """Tokenize text into cleaned, filtered tokens."""
        text = text.lower().strip()
        tokens = re.findall(r"[a-záàâãéèêíïóôõúüçñ]+", text)
        return [
            t for t in tokens
            if len(t) >= _MIN_TOKEN_LEN and t not in _STOP_WORDS
        ]

    def _tokenize_episodes(self, episodes: list[dict]) -> list[list[str]]:
        """Tokenize all episodes into lists of filtered tokens."""
        result: list[list[str]] = []
        for ep in episodes:
            content = ep.get("content", "")
            tokens = self._tokenize_text(content)
            result.append(tokens)
        return result

    # -- Internal: TF-IDF Vocabulary ----------------------------------------

    def _build_vocabulary(self, episode_tokens: list[list[str]]) -> None:
        """Build TF-IDF weighted vocabulary from tokenized episodes.

        TF-IDF = Term Frequency × Inverse Document Frequency
        This identifies tokens that are both frequent and distinctive.
        """
        num_docs = len(episode_tokens)
        if num_docs == 0:
            self._vocabulary = {}
            return

        # Term frequency across all documents
        global_tf: Counter = Counter()
        # Document frequency (in how many episodes does each token appear)
        doc_freq: Counter = Counter()

        for tokens in episode_tokens:
            global_tf.update(tokens)
            unique_tokens = set(tokens)
            doc_freq.update(unique_tokens)

        # Compute TF-IDF
        vocab: dict[str, float] = {}
        for token, tf in global_tf.items():
            df = doc_freq.get(token, 1)
            idf = math.log((num_docs + 1) / (df + 1)) + 1.0
            vocab[token] = (tf / max(sum(global_tf.values()), 1)) * idf

        self._vocabulary = vocab

    # -- Internal: Episode Embeddings ---------------------------------------

    def _compute_embeddings(
        self, episode_tokens: list[list[str]]
    ) -> list[list[float]]:
        """Compute simplified episode embeddings using TF-IDF bag-of-words.

        Each episode is represented as a vector in vocabulary space,
        weighted by TF-IDF scores.  This is a lightweight alternative
        to neural embeddings.
        """
        if not self._vocabulary:
            return []

        # Create ordered vocabulary for consistent vector positions
        vocab_list = sorted(self._vocabulary.keys())
        vocab_index = {t: i for i, t in enumerate(vocab_list)}
        dim = len(vocab_list)

        vectors: list[list[float]] = []
        for tokens in episode_tokens:
            vec = [0.0] * dim
            token_counts = Counter(tokens)
            for token, count in token_counts.items():
                if token in vocab_index:
                    vec[vocab_index[token]] = count * self._vocabulary.get(token, 0.0)
            # L2 normalize
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vec = [v / norm for v in vec]
            vectors.append(vec)

        return vectors

    # -- Internal: Self-Attention -------------------------------------------

    def _compute_self_attention(
        self,
        episode_vectors: list[list[float]],
        personality_vector: list[float],
    ) -> list[list[float]]:
        """Compute scaled dot-product self-attention over episode embeddings.

        Implements the core transformer attention mechanism:
            Attention(Q, K, V) = softmax(QK^T / sqrt(d_k))

        Here Q = K = episode embeddings, so this finds which episodes
        attend to which other episodes (semantic similarity).

        Personality vector modulates attention weights to prefer
        patterns aligned with the Being's identity.

        Parameters
        ----------
        episode_vectors : list[list[float]]
            Episode TF-IDF embeddings.
        personality_vector : list[float]
            Personality traits for modulation.

        Returns
        -------
        list[list[float]]
            Attention weight matrix (softmax-normalized).
        """
        n = len(episode_vectors)
        if n == 0:
            return []

        dim = len(episode_vectors[0]) if episode_vectors[0] else 1
        scale = math.sqrt(dim) or 1.0

        # Compute QK^T (dot-product similarity matrix)
        raw_scores: list[list[float]] = []
        for i in range(n):
            row: list[float] = []
            for j in range(n):
                # Scaled dot-product
                dot = sum(
                    episode_vectors[i][k] * episode_vectors[j][k]
                    for k in range(dim)
                )
                score = dot / scale

                # Position encoding: slight preference for nearby episodes
                distance_penalty = abs(i - j) * 0.01
                score -= distance_penalty

                row.append(score)
            raw_scores.append(row)

        # Apply personality modulation: boost scores for episodes
        # that align with high personality traits
        openness_boost = personality_vector[_OPENNESS_INDEX] if len(personality_vector) > _OPENNESS_INDEX else 0.5
        curiosity_factor = 0.5 + openness_boost * 0.5

        # Softmax normalization per row
        attention: list[list[float]] = []
        for row in raw_scores:
            # Apply curiosity factor as temperature
            scaled = [s * curiosity_factor for s in row]
            max_s = max(scaled) if scaled else 0.0
            exp_scores = [math.exp(s - max_s) for s in scaled]
            total = sum(exp_scores) or 1.0
            attention.append([e / total for e in exp_scores])

        return attention

    # -- Internal: N-gram Pattern Extraction --------------------------------

    def _extract_ngram_patterns(self, episode_tokens: list[list[str]]) -> None:
        """Extract bigram and trigram patterns from tokenized episodes."""
        bigram_counts: Counter = Counter()
        trigram_counts: Counter = Counter()

        for i, tokens in enumerate(episode_tokens):
            for j in range(len(tokens) - 1):
                bigram = (tokens[j], tokens[j + 1])
                bigram_counts[bigram] += 1

            for j in range(len(tokens) - 2):
                trigram = (tokens[j], tokens[j + 1], tokens[j + 2])
                trigram_counts[trigram] += 1

        # Store weighted bigrams (limited to top-k for memory efficiency)
        max_bg_count = max(bigram_counts.values()) if bigram_counts else 1
        self._bigrams = {
            bg: count / max_bg_count
            for bg, count in bigram_counts.most_common(_MAX_BIGRAMS)
        }

        # Store weighted trigrams (limited to top-k)
        max_tg_count = max(trigram_counts.values()) if trigram_counts else 1
        self._trigrams = {
            tg: count / max_tg_count
            for tg, count in trigram_counts.most_common(_MAX_TRIGRAMS)
        }

        # Create LearnedPattern objects from top n-grams
        patterns: list[LearnedPattern] = []

        for (t1, t2), weight in bigram_counts.most_common(min(100, _MAX_BIGRAMS)):
            source_eps: list[int] = []
            for i, tokens in enumerate(episode_tokens):
                for j in range(len(tokens) - 1):
                    if tokens[j] == t1 and tokens[j + 1] == t2:
                        source_eps.append(i)
                        break
            patterns.append(LearnedPattern(
                tokens=[t1, t2],
                weight=weight / max_bg_count,
                frequency=bigram_counts[(t1, t2)],
                source_episodes=source_eps,
            ))

        for (t1, t2, t3), weight in trigram_counts.most_common(min(50, _MAX_TRIGRAMS)):
            source_eps = []
            for i, tokens in enumerate(episode_tokens):
                for j in range(len(tokens) - 2):
                    if tokens[j] == t1 and tokens[j + 1] == t2 and tokens[j + 2] == t3:
                        source_eps.append(i)
                        break
            patterns.append(LearnedPattern(
                tokens=[t1, t2, t3],
                weight=weight / max_tg_count,
                frequency=trigram_counts[(t1, t2, t3)],
                source_episodes=source_eps,
            ))

        # Also add single high-TF-IDF tokens as unigram patterns
        for token, weight in sorted(
            self._vocabulary.items(), key=lambda x: x[1], reverse=True
        )[:_MAX_UNIGRAMS]:
            freq = sum(1 for tokens in episode_tokens if token in tokens)
            patterns.append(LearnedPattern(
                tokens=[token],
                weight=weight,
                frequency=freq,
                source_episodes=[
                    i for i, tokens in enumerate(episode_tokens) if token in tokens
                ],
            ))

        self._patterns = patterns

    # -- Internal: Personality-Weighted Pattern Scoring ----------------------

    def _score_patterns(self, personality_vector: list[float]) -> None:
        """Score patterns weighted by personality alignment.

        Uses the personality vector to modulate pattern importance:
        - High openness → boosts novel/diverse patterns
        - High conscientiousness → boosts recurring/stable patterns
        - High extraversion → boosts social/interactive patterns
        """
        if not self._patterns or not personality_vector:
            return

        # Extract personality dimensions for modulation
        openness = personality_vector[_OPENNESS_INDEX] if len(personality_vector) > _OPENNESS_INDEX else 0.5
        conscientiousness = personality_vector[_CONSCIENTIOUSNESS_INDEX] if len(personality_vector) > _CONSCIENTIOUSNESS_INDEX else 0.5
        curiosity = personality_vector[_CURIOSITY_INDEX] if len(personality_vector) > _CURIOSITY_INDEX else 0.5

        for p in self._patterns:
            base_weight = p.weight

            # Novelty bonus: patterns from diverse sources get boosted by openness
            source_diversity = len(set(p.source_episodes)) / max(len(p.source_episodes), 1)
            novelty_bonus = source_diversity * openness * 0.3

            # Stability bonus: high-frequency patterns get boosted by conscientiousness
            stability_bonus = (p.frequency / 10.0) * conscientiousness * 0.2

            # Curiosity bonus: longer patterns (more information) get boosted
            length_bonus = len(p.tokens) / 5.0 * curiosity * 0.1

            p.weight = base_weight + novelty_bonus + stability_bonus + length_bonus

    # -- Internal: Attention Analysis ---------------------------------------

    def _compute_attention_entropy(self) -> float:
        """Compute Shannon entropy of the attention distribution.

        Low entropy indicates focused learning (few episodes dominate).
        High entropy indicates diffuse attention (all episodes equal).
        """
        if not self._attention_matrix:
            return 0.0

        # Average attention weights across all rows
        n = len(self._attention_matrix)
        avg_weights: list[float] = [0.0] * n
        for row in self._attention_matrix:
            for j, w in enumerate(row):
                avg_weights[j] += w / n

        # Shannon entropy
        entropy = 0.0
        for w in avg_weights:
            if w > 1e-10:
                entropy -= w * math.log(w)

        return entropy

    def _find_attention_clusters(
        self, episodes: list[dict], threshold: float = 0.1
    ) -> list[str]:
        """Find clusters of semantically related episodes via attention.

        Episodes that attend strongly to each other form a cluster,
        which represents a coherent theme in the Being's experience.
        """
        if not self._attention_matrix:
            return []

        n = len(self._attention_matrix)
        visited: set[int] = set()
        clusters: list[list[int]] = []

        for i in range(n):
            if i in visited:
                continue
            cluster = [i]
            visited.add(i)
            for j in range(n):
                if j not in visited and self._attention_matrix[i][j] > threshold:
                    cluster.append(j)
                    visited.add(j)
            if len(cluster) >= 2:
                clusters.append(cluster)

        # Convert clusters to descriptions
        descriptions: list[str] = []
        for cluster in clusters[:5]:
            # Extract common tokens from cluster episodes
            cluster_tokens: Counter = Counter()
            for idx in cluster:
                if idx < len(episodes):
                    content = episodes[idx].get("content", "")
                    tokens = self._tokenize_text(content)
                    cluster_tokens.update(tokens)

            top_words = [w for w, _ in cluster_tokens.most_common(3)]
            if top_words:
                descriptions.append(
                    f"Related themes: {', '.join(top_words)} "
                    f"(cluster of {len(cluster)} episodes)"
                )

        return descriptions

    def _compose_cross_attention_hypotheses(
        self, episodes: list[dict], count: int
    ) -> list[str]:
        """Generate hypotheses by combining high-attention episode pairs."""
        if not self._attention_matrix:
            return []

        hypotheses: list[str] = []
        n = len(self._attention_matrix)

        # Find top attention pairs (excluding self-attention diagonal)
        pairs: list[tuple[int, int, float]] = []
        for i in range(n):
            for j in range(i + 1, n):
                score = self._attention_matrix[i][j]
                pairs.append((i, j, score))

        pairs.sort(key=lambda x: x[2], reverse=True)

        for i, j, score in pairs[:count]:
            if i < len(episodes) and j < len(episodes):
                content_i = episodes[i].get("content", "")[:30]
                content_j = episodes[j].get("content", "")[:30]
                tokens_i = self._tokenize_text(content_i)
                tokens_j = self._tokenize_text(content_j)
                combined = tokens_i[:3] + tokens_j[:3]
                if combined:
                    hypotheses.append(
                        f"hypothesis_about:{' '.join(combined)}"
                    )

        return hypotheses

    def _explore_novel_patterns(
        self,
        episodes: list[dict],
        personality_vector: list[float],
        count: int,
    ) -> list[str]:
        """Generate hypotheses through personality-modulated exploration."""
        hypotheses: list[str] = []
        openness = personality_vector[_OPENNESS_INDEX] if len(personality_vector) > _OPENNESS_INDEX else 0.5

        # Select random episodes weighted by attention entropy
        for _ in range(count):
            if episodes:
                idx = self._rng.randint(0, len(episodes) - 1)
                content = episodes[idx].get("content", "")
                tokens = self._tokenize_text(content)
                if tokens:
                    # Exploration: take random subset of tokens
                    sample_size = max(1, int(len(tokens) * (0.3 + 0.4 * openness)))
                    sample = self._rng.sample(
                        tokens, min(sample_size, len(tokens))
                    )
                    hypotheses.append(f"hypothesis_about:{' '.join(sample)}")
                else:
                    hypotheses.append("reinforce_existing_pattern")
            else:
                hypotheses.append("reinforce_existing_pattern")

        return hypotheses
