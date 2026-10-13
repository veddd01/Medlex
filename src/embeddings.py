"""Embedding generation via Hugging Face sentence-transformer models.

The model name is never hard-coded past this module: everything else
depends only on `get_embedding_model()` and the `Embeddings` interface it
returns (`.embed_documents(list[str])`, `.embed_query(str)`), so swapping
`sentence-transformers/all-MiniLM-L6-v2` for a different model — a larger
one, a domain-tuned one, a multilingual one — is a one-line change here
(or an `EMBEDDING_MODEL_NAME` env var override) with nothing else to edit.

Note: swapping models changes the embedding dimension, which usually means
rebuilding the Pinecone index (see vector_store.create_index, which reads
the dimension from the embedding model itself rather than hard-coding 384).
"""

from __future__ import annotations

import logging
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from src.config import settings

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = settings.embedding_model_name


@lru_cache(maxsize=4)
def get_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> HuggingFaceEmbeddings:
    """Return a cached `HuggingFaceEmbeddings` instance for `model_name`.

    Cached (per model name) because loading a sentence-transformers model
    means downloading and initializing real weights — expensive enough
    that both `ingest.py` and the Flask app should each only pay that cost
    once per process, not once per call.

    Args:
        model_name: Any Hugging Face sentence-embedding model id. Defaults
            to `EMBEDDING_MODEL_NAME` from the environment, which itself
            defaults to "sentence-transformers/all-MiniLM-L6-v2".

    Returns:
        A LangChain `Embeddings` implementation with `.embed_documents()`
        and `.embed_query()`.
    """
    logger.info("Loading embedding model: %s", model_name)
    model = HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs={"normalize_embeddings": True},
    )
    logger.info("Embedding model '%s' ready.", model_name)
    return model


def get_embedding_dimension(model_name: str = DEFAULT_EMBEDDING_MODEL) -> int:
    """Return the output vector dimension of `model_name`.

    Used by `vector_store.create_index` so the Pinecone index dimension
    always matches the embedding model actually in use, instead of a
    hard-coded constant that would silently drift if the model changes.
    """
    model = get_embedding_model(model_name)
    probe_vector = model.embed_query("dimension probe")
    return len(probe_vector)
