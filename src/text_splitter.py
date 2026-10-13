"""Text chunking: split loaded pages into embedding-ready chunks.

Uses `RecursiveCharacterTextSplitter`, which tries a list of separators
(paragraph, then sentence, then word, then character) in order, splitting
on the first one that yields chunks under `chunk_size` — this keeps
sentences/paragraphs intact far more often than a naive fixed-width split.
"""

from __future__ import annotations

import logging
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings

logger = logging.getLogger(__name__)

# Requirement: 500-character chunks with 50-character overlap.
DEFAULT_CHUNK_SIZE = settings.chunk_size
DEFAULT_CHUNK_OVERLAP = settings.chunk_overlap


def split_documents(
    documents: List[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Document]:
    """Split page-level `Document`s into fixed-size, overlapping chunks.

    Each output chunk is itself a `Document` and inherits (and can extend)
    the metadata of the page it came from — `page`, `source`, etc. — via
    `RecursiveCharacterTextSplitter.split_documents`, which LangChain
    propagates automatically.

    Args:
        documents: Page-level documents, typically from `data_loader.load_pdf`.
        chunk_size: Max characters per chunk. Defaults to 500 per spec.
        chunk_overlap: Characters shared between consecutive chunks, so a
            sentence spanning a chunk boundary still appears intact in at
            least one chunk. Defaults to 50 per spec.

    Returns:
        A flat list of chunk `Document`s, ready for embedding.
    """
    if not documents:
        logger.warning("split_documents called with an empty document list.")
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be smaller than "
            f"chunk_size ({chunk_size})."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks = splitter.split_documents(documents)

    # Give every chunk a stable, human-readable id we can reuse as the
    # Pinecone vector id (source file + page + position on that page).
    per_page_counter: dict[int, int] = {}
    for chunk in chunks:
        page = chunk.metadata.get("page", -1)
        idx = per_page_counter.get(page, 0)
        chunk.metadata["chunk_index_on_page"] = idx
        per_page_counter[page] = idx + 1

    logger.info(
        "Split %d page(s) into %d chunk(s) (chunk_size=%d, overlap=%d).",
        len(documents), len(chunks), chunk_size, chunk_overlap,
    )
    return chunks
