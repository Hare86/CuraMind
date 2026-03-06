"""
Embedding service using BGE-large-en-v1.5.
Also provides sparse vector computation (BM25-like TF-IDF) for hybrid search.
"""
import math
import re
from collections import Counter
from functools import lru_cache

import numpy as np

from app.core.config import settings

# Common English stop words to exclude from sparse vectors
STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did "
    "will would could should may might shall can at in on of to for "
    "with by from up about into through during before after above below "
    "between out off over under again further then once here there when "
    "where why how all both each few more most other some such no nor not "
    "only own same so than too very just".split()
)


class EmbeddingService:
    """
    Generates dense embeddings (BGE-large) and sparse vectors (TF-IDF approximation).
    Single Responsibility: embedding computation only.
    """

    def __init__(self):
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                device="cpu",
            )
        return self._model

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string. Returns normalized float vector."""
        model = self._load_model()
        # BGE models perform better with instruction prefix for queries
        prefixed = f"Represent this sentence for searching relevant passages: {text}"
        vector = model.encode(prefixed, normalize_embeddings=True)
        return vector.tolist()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Batch embed documents. Returns list of normalized float vectors."""
        model = self._load_model()
        vectors = model.encode(
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]

    def compute_sparse_vector(
        self, text: str
    ) -> tuple[list[int], list[float]]:
        """
        Compute a BM25-approximated sparse vector.
        Maps tokens to integer indices via hash, returns (indices, values).
        Compatible with Qdrant's SparseVector format.
        """
        tokens = _tokenize(text)
        if not tokens:
            return [], []

        token_counts = Counter(tokens)
        total_tokens = len(tokens)

        indices = []
        values = []
        seen_indices: set[int] = set()

        for token, count in token_counts.items():
            idx = _token_to_index(token)
            if idx in seen_indices:
                continue
            seen_indices.add(idx)

            tf = count / total_tokens
            idf = math.log(1 + 1 / (count + 1))  # Approximation without corpus stats
            score = tf * idf

            indices.append(idx)
            values.append(float(score))

        return indices, values


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens = re.findall(r"\b[a-z][a-z0-9]{1,}\b", text)
    return [t for t in tokens if t not in STOP_WORDS and len(t) >= 2]


def _token_to_index(token: str) -> int:
    """Map token to a fixed-size vocabulary index via consistent hashing."""
    VOCAB_SIZE = 30_000
    return abs(hash(token)) % VOCAB_SIZE


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
