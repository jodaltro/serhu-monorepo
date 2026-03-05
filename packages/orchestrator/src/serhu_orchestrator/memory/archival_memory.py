"""Archival Memory – Qdrant vector store (the "Disk").

Implements the long-term semantic memory tier of the MemGPT-like architecture.
Stores embeddings of past interactions and learned knowledge for similarity-based
retrieval, enabling multi-hop reasoning across the Being's lifetime.

References:
    - MAGMA architecture: https://arxiv.org/html/2601.03236v1
    - Qdrant client: https://qdrant.tech/documentation/
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    KeywordIndexParams,
    PointStruct,
    VectorParams,
)


@dataclass
class ArchivalEntry:
    """A record stored in archival (vector) memory."""

    content: str
    vector: list[float]
    memory_type: str = "episodic"  # episodic | semantic | causal
    timestamp: float = field(default_factory=time.time)
    metadata: dict | None = None
    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex)


class ArchivalMemory:
    """Long-term vector memory backed by Qdrant.

    Acts as the "Disk" in the MemGPT OS analogy.  Each entry is stored as a
    vector embedding with rich metadata for filtered retrieval.

    Parameters
    ----------
    url : str
        Qdrant cluster endpoint.
    api_key : str
        Qdrant API key.
    collection_name : str
        Name of the Qdrant collection to use.
    vector_size : int
        Dimensionality of the embedding vectors (default 384 for
        all-MiniLM-L6-v2 style models).
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        collection_name: str = "serhu_archival",
        vector_size: int = 384,
    ) -> None:
        self._client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._ensure_collection()

    # -- lifecycle -----------------------------------------------------------

    def _ensure_collection(self) -> None:
        """Create the collection if it doesn't already exist."""
        existing = [c.name for c in self._client.get_collections().collections]
        if self.collection_name not in existing:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )
            # Create index for memory_type field to enable filtering
            self._client.create_payload_index(
                collection_name=self.collection_name,
                field_name="memory_type",
                field_schema=KeywordIndexParams(type="keyword"),
            )

    # -- public API ----------------------------------------------------------

    def store(self, entry: ArchivalEntry) -> str:
        """Persist an entry to Qdrant. Returns the point id."""
        point_id = self._deterministic_id(entry.entry_id)
        payload = {
            "content": entry.content,
            "memory_type": entry.memory_type,
            "timestamp": entry.timestamp,
            **(entry.metadata or {}),
        }
        self._client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=entry.vector,
                    payload=payload,
                )
            ],
        )
        return entry.entry_id

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[dict]:
        """Semantic similarity search.

        Parameters
        ----------
        query_vector : list[float]
            The embedding vector to search with.
        top_k : int
            Number of results to return.
        memory_type : str | None
            Optional filter on memory_type field.

        Returns
        -------
        list[dict]
            Matching entries as payload dicts with ``score`` added.
        """
        query_filter = None
        if memory_type:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(value=memory_type),
                    )
                ]
            )

        results = self._client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )
        return [
            {**hit.payload, "score": hit.score}
            for hit in results.points
        ]

    def delete_collection(self) -> None:
        """Remove the entire collection (for cleanup / testing)."""
        self._client.delete_collection(collection_name=self.collection_name)

    def count(self) -> int:
        """Return the number of points in the collection."""
        info = self._client.get_collection(self.collection_name)
        return info.points_count

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _deterministic_id(entry_id: str) -> str:
        """Create a deterministic UUID-style string from an entry_id.

        Qdrant accepts UUID strings as point ids. We hash the entry_id
        to produce a valid UUID-formatted identifier.
        """
        h = hashlib.sha256(entry_id.encode()).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"
