"""
Optional cross-encoder reranker.
Enabled via settings.RERANKER_ENABLED flag.
Falls back to score-sorted hybrid results if disabled.
"""
from app.rag.hybrid_search import RetrievedChunk


class CrossEncoderReranker:
    """
    Reranks retrieved chunks using a cross-encoder model.
    Lazy-loads the model on first use to avoid startup overhead.
    """

    MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self):
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.MODEL_NAME)

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return chunks

        self._load_model()

        pairs = [(query, chunk.content) for chunk in chunks]
        scores = self._model.predict(pairs)

        for chunk, score in zip(chunks, scores):
            chunk.score = float(score)

        return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_k]


class PassthroughReranker:
    """No-op reranker — returns top_k by hybrid score."""

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        return sorted(chunks, key=lambda c: c.score, reverse=True)[:top_k]


def get_reranker(enabled: bool = False):
    if enabled:
        return CrossEncoderReranker()
    return PassthroughReranker()
