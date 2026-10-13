"""Cross-encoder re-ranking for retrieved chunks."""
from typing import Any, Dict, List

def rerank_chunks(question: str, chunks: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
    """Re-rank chunks using cross-encoder similarity.
    
    Falls back to score-based sorting if cross-encoder is unavailable.
    """
    # Try to use sentence-transformers CrossEncoder
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        pairs = [(question, chunk["text"]) for chunk in chunks]
        scores = model.predict(pairs)
        for chunk, score in zip(chunks, scores):
            chunk["rerank_score"] = float(score)
        chunks.sort(key=lambda c: c["rerank_score"], reverse=True)
    except Exception:
        # Fallback: just use original similarity scores
        chunks.sort(key=lambda c: c.get("score", 0), reverse=True)
    
    return chunks[:top_n]
