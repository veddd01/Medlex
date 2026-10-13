"""Hybrid search combining BM25 keyword matching with vector similarity."""
from typing import Any, Dict, List

def hybrid_search(question: str, vector_chunks: List[Dict[str, Any]], alpha: float = 0.7) -> List[Dict[str, Any]]:
    """Combine vector similarity scores with BM25 keyword scores.
    
    alpha: weight for vector score (1-alpha for BM25)
    """
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        # If rank_bm25 not installed, return vector results as-is
        return vector_chunks
    
    if not vector_chunks:
        return []
    
    # Build BM25 index from chunk texts
    tokenized = [chunk["text"].lower().split() for chunk in vector_chunks]
    bm25 = BM25Okapi(tokenized)
    
    query_tokens = question.lower().split()
    bm25_scores = bm25.get_scores(query_tokens)
    
    # Normalize BM25 scores to [0, 1]
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    
    for chunk, bm25_score in zip(vector_chunks, bm25_scores):
        normalized_bm25 = bm25_score / max_bm25
        chunk["hybrid_score"] = alpha * chunk.get("score", 0) + (1 - alpha) * normalized_bm25
    
    vector_chunks.sort(key=lambda c: c["hybrid_score"], reverse=True)
    return vector_chunks
