"""Value Model – Lightweight reward predictor trained during sleep.

Predicts expected reward for a (state, action) pair using a simple linear
model over hand-crafted features.  Trained on experiences collected during
dream rollouts and real interactions, the ValueModel allows the online
planner to cheaply pre-screen candidate responses and only run full AIXI
rollouts on the top-K (default 3), dramatically cutting planning cost.

Training happens at the end of the sleep cycle (after NeuralEngine
training and semantization) using ``fit(pairs, targets)``.  Each instance
carries a content-based ``version`` hash and quality ``metrics`` for
tracking model evolution across sleep cycles, following the same
versioning pattern as :class:`WorldModel`.

References:
    - Value function approximation: https://arxiv.org/abs/1911.02150
    - AIXI planning cost: https://www.alignmentforum.org/w/aixi
"""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValueModel:
    """Simple linear reward predictor: ``V(state, action) → reward_pred``.

    Uses bag-of-words features over the action text combined with a
    personality-state vector to predict expected reward.  The model is
    intentionally simple (no deep learning) so it trains in microseconds
    during sleep and runs in nanoseconds during online planning.

    Attributes
    ----------
    weights : dict[str, float]
        Feature name → learned weight mapping.
    bias : float
        Model bias term.
    version : str
        Content-based hash for versioning the trained artifact.
    metrics : dict[str, float]
        Quality metrics (e.g. ``mse``, ``samples``, ``r_squared``).
    learning_rate : float
        Step size for gradient updates during ``fit()``.
    """

    weights: dict[str, float] = field(default_factory=dict)
    bias: float = 0.0
    version: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    learning_rate: float = 0.01

    @property
    def is_trained(self) -> bool:
        """Whether the model has been fitted on data."""
        return len(self.weights) > 0

    # -- training ------------------------------------------------------------

    def fit(
        self,
        pairs: list[tuple[list[float], str]],
        targets: list[float],
        *,
        epochs: int = 10,
    ) -> dict[str, float]:
        """Train the value model on (state, action) → reward pairs.

        Parameters
        ----------
        pairs : list[tuple[list[float], str]]
            Each element is ``(personality_vector, action_text)``.
        targets : list[float]
            Target reward values corresponding to each pair.
        epochs : int
            Number of passes over the training data.

        Returns
        -------
        dict[str, float]
            Training metrics: ``mse``, ``samples``, ``r_squared``.
        """
        if not pairs or not targets or len(pairs) != len(targets):
            self.metrics = {"mse": 0.0, "samples": 0, "r_squared": 0.0}
            self.version = self._compute_version()
            return dict(self.metrics)

        # Build feature representations
        feature_rows = [self._featurize(state, action) for state, action in pairs]

        # Collect all feature names across training data
        all_features: set[str] = set()
        for row in feature_rows:
            all_features.update(row.keys())

        # Initialize missing weights to zero
        for feat in all_features:
            if feat not in self.weights:
                self.weights[feat] = 0.0

        # Mini-batch gradient descent
        n = len(targets)
        for _epoch in range(epochs):
            total_loss = 0.0
            for features, target in zip(feature_rows, targets):
                pred = self._predict_from_features(features)
                error = pred - target
                total_loss += error * error

                # Update weights
                for feat, val in features.items():
                    self.weights[feat] -= self.learning_rate * error * val / n
                self.bias -= self.learning_rate * error / n

        # Compute final metrics
        predictions = [self._predict_from_features(f) for f in feature_rows]
        mse = sum((p - t) ** 2 for p, t in zip(predictions, targets)) / n

        mean_target = sum(targets) / n
        ss_tot = sum((t - mean_target) ** 2 for t in targets)
        ss_res = sum((p - t) ** 2 for p, t in zip(predictions, targets))
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        self.metrics = {
            "mse": mse,
            "samples": float(n),
            "r_squared": r_squared,
        }
        self.version = self._compute_version()

        logger.info(
            "ValueModel trained: samples=%d, mse=%.6f, R²=%.4f, features=%d, version=%s",
            n, mse, r_squared, len(self.weights), self.version,
        )
        return dict(self.metrics)

    # -- prediction ----------------------------------------------------------

    def predict(self, state: list[float], action: str) -> float:
        """Predict reward for a (state, action) pair.

        Parameters
        ----------
        state : list[float]
            Personality vector (72 dims).
        action : str
            Action text (AIXI action label or response text).

        Returns
        -------
        float
            Predicted reward.
        """
        features = self._featurize(state, action)
        return self._predict_from_features(features)

    def rank(
        self,
        state: list[float],
        actions: list[str],
        top_k: int = 3,
    ) -> list[tuple[int, str, float]]:
        """Rank actions by predicted reward and return the top-K.

        Parameters
        ----------
        state : list[float]
            Personality vector.
        actions : list[str]
            Candidate action texts.
        top_k : int
            Number of top candidates to return.

        Returns
        -------
        list[tuple[int, str, float]]
            List of ``(original_index, action, predicted_reward)``
            sorted by predicted reward descending, truncated to *top_k*.
        """
        scored = [
            (i, action, self.predict(state, action))
            for i, action in enumerate(actions)
        ]
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_k]

    # -- feature engineering -------------------------------------------------

    @staticmethod
    def _featurize(state: list[float], action: str) -> dict[str, float]:
        """Build a sparse feature vector from state and action.

        Features include:
        - ``act:<token>``: Bag-of-words from the action text.
        - ``pv_mean``: Mean of the personality vector.
        - ``pv_std``: Standard deviation of the personality vector.
        - ``act_len``: Normalized action length.
        """
        features: dict[str, float] = {}

        # Action token features
        tokens = action.lower().replace("_", " ").split()
        for token in tokens:
            if len(token) > 1:
                key = f"act:{token}"
                features[key] = features.get(key, 0.0) + 1.0

        # Personality vector summary features
        if state:
            mean = sum(state) / len(state)
            variance = sum((x - mean) ** 2 for x in state) / len(state)
            features["pv_mean"] = mean
            features["pv_std"] = math.sqrt(variance) if variance > 0 else 0.0
        else:
            features["pv_mean"] = 0.0
            features["pv_std"] = 0.0

        # Action length feature (normalized)
        features["act_len"] = min(len(tokens) / 10.0, 1.0)

        return features

    # -- internal helpers ----------------------------------------------------

    def _predict_from_features(self, features: dict[str, float]) -> float:
        """Compute dot product of features with weights + bias."""
        score = self.bias
        for feat, val in features.items():
            score += self.weights.get(feat, 0.0) * val
        return score

    def _compute_version(self) -> str:
        """Compute a content-based hash for this model."""
        content = repr(sorted(self.weights.items())) + repr(self.bias)
        return hashlib.sha256(content.encode()).hexdigest()[:12]
