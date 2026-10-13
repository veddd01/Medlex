"""Retrieval layer: turn a raw question into relevant, cited chunks.

This is the "embed the question -> search Pinecone -> top-5 chunks" half
of the workflow in the spec. `rag_pipeline.py` calls this, then hands the
result to `llm.py` for generation — this module never talks to the LLM.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.embeddings import get_embedding_model
from src.vector_store import search_documents

logger = logging.getLogger(__name__)


def retrieve_relevant_chunks(
    question: str,
    top_k: Optional[int] = None,
    index_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Embed `question` and return its top-k most relevant chunks.

    Args:
        question: The user's raw question text.
        top_k: How many chunks to retrieve. Defaults to `settings.top_k`
            (5, per spec) inside `search_documents`.
        index_name: Which Pinecone index to search. Defaults to
            `settings.pinecone_index_name`.

    Returns:
        A list of `{"text", "page", "source", "score"}` dicts, most
        relevant first. Empty if the question is blank or nothing matched.
    """
    question = (question or "").strip()
    if not question:
        logger.warning("retrieve_relevant_chunks called with an empty question.")
        return []

    embedder = get_embedding_model()
    query_vector = embedder.embed_query(question)

    chunks = search_documents(query_vector, index_name=index_name, top_k=top_k)
    logger.info("Retrieved %d chunk(s) for question: %r", len(chunks), _truncate(question))
    return chunks


def format_context(chunks: List[Dict[str, Any]]) -> str:
    """Join retrieved chunks into a single context string for the LLM prompt.

    Each chunk is prefixed with its page number so the LLM prompt itself
    carries provenance, not just the API response — useful if you extend
    the prompt to ask the model to reference pages directly.
    """
    if not chunks:
        return ""
    return "\n\n".join(
        f"[Page {chunk['page']}] {chunk['text']}" for chunk in chunks
    )


def _truncate(text: str, max_len: int = 80) -> str:
    return text if len(text) <= max_len else text[: max_len - 1] + "…"
