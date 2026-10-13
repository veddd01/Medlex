"""Pinecone vector database integration.

Provides three reusable functions per spec — `create_index()`,
`upsert_documents()`, `search_documents()` — built directly on the
Pinecone SDK (not the LangChain VectorStore wrapper) so the ID scheme,
batching, and metadata shape stay fully explicit and inspectable.

Uses the current class-based Pinecone SDK (`pinecone>=9`):
    pc = Pinecone(api_key=...)
    pc.create_index(name=..., dimension=..., spec=ServerlessSpec(...))
    index = pc.index(name=...)
    index.upsert(vectors=[...]) / index.query(vector=..., top_k=...)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeException, UnauthorizedException

from src.config import settings
from src.embeddings import get_embedding_dimension, get_embedding_model

logger = logging.getLogger(__name__)

_INDEX_READY_TIMEOUT_S = 60
_INDEX_READY_POLL_S = 2
_DEFAULT_UPSERT_BATCH_SIZE = 100


class VectorStoreError(RuntimeError):
    """Base class for vector-store-related failures."""


class PineconeAuthError(VectorStoreError):
    """Raised when the Pinecone API key is missing or invalid."""


class PineconeConnectionError(VectorStoreError):
    """Raised when Pinecone can't be reached or a request fails server-side."""


_client: Optional[Pinecone] = None


def get_client() -> Pinecone:
    """Return a process-wide cached Pinecone client.

    Raises:
        ConfigError: If PINECONE_API_KEY / PINECONE_ENVIRONMENT are unset
            (raised by `settings.require_pinecone()`).
        PineconeAuthError: If the SDK itself rejects the key at construction.
    """
    global _client
    if _client is not None:
        return _client

    settings.require_pinecone()
    try:
        _client = Pinecone(api_key=settings.pinecone_api_key)
    except UnauthorizedException as exc:
        raise PineconeAuthError(f"Pinecone rejected the API key: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - normalize any SDK-level failure
        raise PineconeConnectionError(f"Failed to initialize Pinecone client: {exc}") from exc
    return _client


def create_index(
    index_name: Optional[str] = None,
    dimension: Optional[int] = None,
    metric: str = "cosine",
) -> None:
    """Create the Pinecone index if it doesn't already exist, then wait until ready.

    Args:
        index_name: Defaults to `settings.pinecone_index_name`.
        dimension: Defaults to the active embedding model's output size
            (see `embeddings.get_embedding_dimension`), so the index always
            matches whatever model is actually configured.
        metric: Similarity metric. "cosine" is the standard choice for
            normalized sentence-transformer embeddings.
    """
    index_name = index_name or settings.pinecone_index_name
    dimension = dimension or get_embedding_dimension()
    pc = get_client()

    try:
        if pc.has_index(index_name):
            logger.info("Pinecone index '%s' already exists; skipping creation.", index_name)
            return

        logger.info(
            "Creating Pinecone index '%s' (dimension=%d, metric=%s, cloud=%s, region=%s)...",
            index_name, dimension, metric, settings.pinecone_cloud, settings.pinecone_environment,
        )
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(
                cloud=settings.pinecone_cloud,
                region=settings.pinecone_environment,
            ),
        )
    except UnauthorizedException as exc:
        raise PineconeAuthError(
            "Pinecone rejected the API key while creating the index. "
            "Double-check PINECONE_API_KEY in .env."
        ) from exc
    except PineconeException as exc:
        raise PineconeConnectionError(
            f"Failed to create Pinecone index '{index_name}': {exc}"
        ) from exc

    _wait_until_ready(pc, index_name)
    logger.info("Pinecone index '%s' is ready.", index_name)


def _wait_until_ready(pc: Pinecone, index_name: str, timeout_s: int = _INDEX_READY_TIMEOUT_S) -> None:
    """Poll `describe_index` until `status.ready` is True or `timeout_s` elapses."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        status = pc.describe_index(index_name).status
        if status.ready:
            return
        time.sleep(_INDEX_READY_POLL_S)
    raise PineconeConnectionError(
        f"Index '{index_name}' did not report ready within {timeout_s}s. "
        "It may still be initializing — check the Pinecone console."
    )


def upsert_documents(
    chunks: Sequence[Document],
    index_name: Optional[str] = None,
    batch_size: int = _DEFAULT_UPSERT_BATCH_SIZE,
) -> int:
    """Embed `chunks` and upload them to Pinecone.

    Each vector is stored with `metadata = {"text", "page", "source"}` per
    spec (embedding + text + page number), keyed by a deterministic id of
    the form `<source-stem>-p<page>-c<chunk-index-on-page>` so re-running
    ingestion on the same PDF overwrites the same vectors rather than
    duplicating them.

    Args:
        chunks: Chunked `Document`s from `text_splitter.split_documents`.
        index_name: Defaults to `settings.pinecone_index_name`.
        batch_size: Chunks embedded/upserted per batch.

    Returns:
        Total number of vectors upserted.
    """
    if not chunks:
        logger.warning("upsert_documents called with no chunks; nothing to do.")
        return 0

    index_name = index_name or settings.pinecone_index_name
    pc = get_client()

    try:
        index = pc.index(name=index_name)
    except PineconeException as exc:
        raise PineconeConnectionError(f"Could not open index '{index_name}': {exc}") from exc

    embedder = get_embedding_model()
    total_upserted = 0
    chunks = list(chunks)

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start: batch_start + batch_size]
        texts = [doc.page_content for doc in batch]

        try:
            embedded_vectors = embedder.embed_documents(texts)
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(
                f"Embedding failed for batch starting at index {batch_start}: {exc}"
            ) from exc

        vectors: List[Dict[str, Any]] = []
        for i, (doc, values) in enumerate(zip(batch, embedded_vectors)):
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", -1)
            chunk_idx = doc.metadata.get("chunk_index_on_page", i)
            vector_id = f"{Path(str(source)).stem}-p{page}-c{chunk_idx}"
            vectors.append({
                "id": vector_id,
                "values": values,
                "metadata": {
                    "text": doc.page_content,
                    "page": page,
                    "source": str(source),
                },
            })

        try:
            index.upsert(vectors=vectors)
        except UnauthorizedException as exc:
            raise PineconeAuthError("Pinecone rejected the API key during upsert.") from exc
        except PineconeException as exc:
            raise PineconeConnectionError(
                f"Upsert failed for batch starting at index {batch_start}: {exc}"
            ) from exc

        total_upserted += len(vectors)
        logger.info("Upserted %d/%d chunks...", total_upserted, len(chunks))

    logger.info("Finished upserting %d chunk(s) into index '%s'.", total_upserted, index_name)
    return total_upserted


def search_documents(
    query_embedding: List[float],
    index_name: Optional[str] = None,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return the `top_k` chunks most similar to `query_embedding`.

    Args:
        query_embedding: A single query vector (e.g. from
            `embeddings.get_embedding_model().embed_query(question)`).
        index_name: Defaults to `settings.pinecone_index_name`.
        top_k: Defaults to `settings.top_k` (5, per spec).

    Returns:
        A list (possibly empty) of dicts: `{"text", "page", "source", "score"}`,
        ordered most-similar first. An empty list means no vectors matched
        (e.g. the index is empty because ingestion hasn't run yet) — callers
        should treat that as "no context available," not an error.
    """
    index_name = index_name or settings.pinecone_index_name
    top_k = top_k or settings.top_k
    pc = get_client()

    try:
        index = pc.index(name=index_name)
        response = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    except UnauthorizedException as exc:
        raise PineconeAuthError("Pinecone rejected the API key during search.") from exc
    except PineconeException as exc:
        raise PineconeConnectionError(f"Search failed against index '{index_name}': {exc}") from exc

    results: List[Dict[str, Any]] = []
    for match in response.matches:
        metadata = match.metadata or {}
        results.append({
            "text": metadata.get("text", ""),
            "page": metadata.get("page", -1),
            "source": metadata.get("source", "unknown"),
            "score": match.score,
        })

    if not results:
        logger.warning("No matches found in index '%s' for this query.", index_name)

    return results
