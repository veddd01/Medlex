"""End-to-end RAG orchestration.

Implements the workflow from the spec exactly:

    User Question
        -> embed question
        -> search Pinecone
        -> retrieve top-5 chunks
        -> pass context + question into FLAN-T5
        -> final answer

`RAGPipeline` loads the embedding model and FLAN-T5 once (in `__init__`)
and reuses them for every `.answer()` call — `app.py` constructs exactly
one instance at startup, not one per request.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.llm import DEFAULT_LLM_MODEL, GenerationError, LLMLoadError, generate_answer, load_model
from src.retriever import format_context, retrieve_relevant_chunks
from src.vector_store import PineconeAuthError, PineconeConnectionError, VectorStoreError

logger = logging.getLogger(__name__)

NO_CONTEXT_MESSAGE = (
    "I couldn't find anything relevant to that question in the medical "
    "encyclopedia this assistant is grounded in. Please try rephrasing, "
    "or consult a healthcare professional for guidance."
)


class RAGPipeline:
    """Loads models once; answers questions many times.

    Attributes:
        llm_model_name: FLAN-T5 checkpoint in use (for logging/diagnostics).
    """

    def __init__(self, llm_model_name: Optional[str] = None) -> None:
        self.llm_model_name = llm_model_name or DEFAULT_LLM_MODEL
        logger.info("Initializing RAG pipeline (this loads the LLM into memory)...")
        self._text_generator = load_model(self.llm_model_name)
        logger.info("RAG pipeline ready (llm=%s).", self.llm_model_name)

    def answer(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """Answer `question`, grounded in the top-k retrieved chunks.

        Args:
            question: Raw user question text.
            top_k: Overrides the configured number of chunks to retrieve.

        Returns:
            A dict with:
                answer (str): The generated answer.
                sources (list[dict]): The chunks the answer was grounded
                    in — each with `page`, `source`, `score`, and `excerpt`
                    (the retrieved text itself) — so the UI can show real
                    citations, not just a page number.
                grounded (bool): False if no relevant chunks were found
                    (in which case `answer` is a fixed "no context" message
                    rather than a model hallucination).
        """
        question = (question or "").strip()
        if not question:
            raise ValueError("question must be a non-empty string.")

        # Retrieve more chunks initially for better reranking context (e.g. 15 if not specified)
        fetch_k = top_k if top_k is not None else 15
        chunks = retrieve_relevant_chunks(question, top_k=fetch_k)

        # Apply hybrid search
        from src.hybrid_search import hybrid_search
        chunks = hybrid_search(question, chunks)

        # Filter out low-relevance chunks
        from src.config import settings
        # We can still use the base score or hybrid_score
        chunks = [c for c in chunks if c.get("hybrid_score", c.get("score", 0)) >= settings.min_score]

        # Re-rank chunks using cross-encoder, pick top 5
        from src.reranker import rerank_chunks
        chunks = rerank_chunks(question, chunks, top_n=5)

        if not chunks:
            logger.info("No relevant chunks found; returning the no-context fallback.")
            return {"answer": NO_CONTEXT_MESSAGE, "sources": [], "grounded": False}

        context = format_context(chunks)
        answer_text = generate_answer(context, question, text_generator=self._text_generator)

        sources = [
            {
                "page": chunk["page"],
                "source": chunk["source"],
                "score": chunk["score"],
                "excerpt": chunk["text"],
            }
            for chunk in chunks
        ]
        return {"answer": answer_text, "sources": sources, "grounded": True}


# ------------------------------------------------------------------------
# Module-level convenience wrapper
# ------------------------------------------------------------------------
#
# `app.py` uses the `RAGPipeline` class directly so the LLM loads exactly
# once at process startup. This function is offered for scripts/tests that
# just want a single one-off call and don't care about reuse; it relies on
# `load_model`'s own `lru_cache`, so repeated calls within one process
# still don't reload the model.

def answer_question(question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
    """One-off convenience wrapper around `RAGPipeline` for scripts/tests."""
    return RAGPipeline().answer(question, top_k=top_k)


__all__ = [
    "RAGPipeline",
    "answer_question",
    "NO_CONTEXT_MESSAGE",
    "GenerationError",
    "LLMLoadError",
    "VectorStoreError",
    "PineconeAuthError",
    "PineconeConnectionError",
]
