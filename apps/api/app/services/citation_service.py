"""
Citation service — formats and validates citations extracted from retrieved chunks.
"""
import re

from app.rag.hybrid_search import RetrievedChunk
from app.schemas.citation import Citation


class CitationService:
    """
    Builds structured Citation objects from retrieved chunks.
    Ensures every citation has sufficient metadata for academic use.
    """

    def build_citations(self, chunks: list[RetrievedChunk]) -> list[Citation]:
        """Build citation list indexed from [1]."""
        return [
            Citation(
                index=idx + 1,
                document_title=chunk.document_title or "Unknown Source",
                page_number=chunk.page_number,
                source_url=chunk.source_url,
                kb_name=chunk.kb_name,
                chunk_excerpt=self._truncate_excerpt(chunk.content),
                relevance_score=round(chunk.score, 4),
            )
            for idx, chunk in enumerate(chunks)
        ]

    def inject_citation_markers(self, text: str, citations: list[Citation]) -> str:
        """
        Ensure citation markers [N] in the text match available citations.
        Strips any out-of-range markers.
        """
        valid_indices = {c.index for c in citations}

        def replace_marker(match: re.Match) -> str:
            idx = int(match.group(1))
            return f"[{idx}]" if idx in valid_indices else ""

        return re.sub(r"\[(\d+)\]", replace_marker, text)

    @staticmethod
    def _truncate_excerpt(content: str, max_length: int = 250) -> str:
        if len(content) <= max_length:
            return content
        return content[:max_length].rsplit(" ", 1)[0] + "..."
