from app.schemas.query import QueryMode

SYSTEM_PROMPT = """You are an academic psychology assistant for a research and learning platform.
Your role is to provide strictly evidence-based, educational information grounded exclusively
in the provided source documents.

STRICT RULES:
1. Only use information from the provided source documents. Do not add any external knowledge.
2. Always include inline citations using the format [1], [2], etc., matching the sources provided.
3. If the sources do not contain sufficient information, clearly state this limitation.
4. Never provide personal diagnoses, prescribe medication, or act as a therapist.
5. Maintain academic tone appropriate for psychology professionals and students.
6. For clinical topics, always recommend consulting a licensed professional."""

MODE_INSTRUCTIONS: dict[QueryMode, str] = {
    "question_answer": (
        "Provide a clear, well-structured academic answer. "
        "Use headings where appropriate. Include citations for every factual claim."
    ),
    "mcq": (
        "Generate multiple-choice questions based on the provided content. "
        "Each question must be directly supported by the source documents."
    ),
    "case_study": (
        "Generate a realistic clinical case study based on the provided content. "
        "Include presenting symptoms, clinical considerations, and treatment approaches. "
        "Do not include a specific diagnosis — only differential considerations."
    ),
    "long_academic": (
        "Write a comprehensive academic essay response with introduction, body sections, "
        "and conclusion. Use APA-style inline citations."
    ),
    "symptoms_to_disorder": (
        "Based on the symptoms described, explain which psychological disorders present "
        "with these features according to the source documents. Include diagnostic criteria. "
        "This is for educational purposes only, not clinical diagnosis."
    ),
    "disorder_to_symptoms": (
        "Explain the characteristic symptoms, presentation patterns, and diagnostic criteria "
        "for the specified disorder, strictly based on the provided sources."
    ),
    "treatment_approach": (
        "Explain the evidence-based treatment approaches described in the sources. "
        "Include therapeutic modalities, protocols, and expected outcomes where documented."
    ),
}


def build_rag_prompt(
    query: str,
    mode: QueryMode,
    context_chunks: list[dict],
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) tuple.

    Each context_chunk must have:
        - content: str
        - citation_index: int
        - document_title: str
        - page_number: int | None
    """
    mode_instruction = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["question_answer"])

    sources_block = _format_sources_block(context_chunks)

    user_prompt = f"""TASK: {mode_instruction}

SOURCE DOCUMENTS:
{sources_block}

USER QUERY:
{query}

INSTRUCTIONS:
- Use ONLY the source documents above to formulate your response.
- Cite sources inline as [1], [2], etc.
- If no relevant information exists in the sources, state:
  "No verified information found in the current knowledge base."
"""
    return SYSTEM_PROMPT, user_prompt


def _format_sources_block(context_chunks: list[dict]) -> str:
    if not context_chunks:
        return "[No source documents retrieved]"

    lines = []
    for chunk in context_chunks:
        idx = chunk["citation_index"]
        title = chunk.get("document_title", "Unknown Source")
        page = chunk.get("page_number")
        content = chunk.get("content", "")
        page_str = f" (Page {page})" if page else ""
        lines.append(f"[{idx}] {title}{page_str}:\n{content}\n")

    return "\n".join(lines)


def build_safety_classification_prompt(query: str) -> str:
    return f"""Classify the following user query for a psychology educational platform.

Respond with ONLY one of these labels:
- ALLOWED — educational, academic, research-oriented psychology question
- BLOCKED_DIAGNOSIS — user is requesting a personal diagnosis
- BLOCKED_MEDICATION — user is asking for medication advice or prescriptions
- BLOCKED_THERAPY — user wants the AI to act as their therapist or counselor
- BLOCKED_SELFHARM — content relates to self-harm, suicidal ideation, or crisis

Query: {query}

Label:"""


def build_query_rewrite_prompt(query: str) -> str:
    return f"""You are a psychology research assistant. Rewrite the following query to be more
precise and suitable for academic document retrieval. Expand abbreviations, add relevant
psychological terminology, and clarify the intent. Return ONLY the rewritten query.

Original query: {query}

Rewritten query:"""
