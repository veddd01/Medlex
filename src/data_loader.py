"""Data ingestion: load a PDF into LangChain `Document` objects.

One `Document` is produced per page (PyPDFLoader's default `mode="page"`),
each with `metadata["page"]` set — this is what lets later stages (see
text_splitter.py, vector_store.py) attach a page number to every chunk, so
the chatbot can cite where an answer came from.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Union

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class PDFNotFoundError(FileNotFoundError):
    """Raised when the source PDF does not exist at the given path."""


class PDFLoadError(RuntimeError):
    """Raised when the PDF exists but cannot be parsed (corrupt, encrypted, etc.)."""


def load_pdf(file_path: Union[str, Path]) -> List[Document]:
    """Load every page of a PDF into a list of LangChain `Document`s.

    Args:
        file_path: Path to the source PDF (e.g. a 700+ page medical
            encyclopedia).

    Returns:
        One `Document` per page. `Document.page_content` holds the
        extracted text; `Document.metadata` includes at least `source`
        (the file path) and `page` (0-indexed page number, as set by
        PyPDFLoader).

    Raises:
        PDFNotFoundError: If `file_path` does not exist.
        PDFLoadError: If the file exists but PyPDFLoader fails to parse it
            (e.g. corrupted or password-protected without a password).
    """
    path = Path(file_path)
    if not path.exists():
        raise PDFNotFoundError(
            f"PDF not found at '{path}'. Place your medical encyclopedia "
            f"PDF there, or pass a different path with --pdf-path "
            f"(see `python ingest.py --help`)."
        )
    if path.suffix.lower() != ".pdf":
        logger.warning("File '%s' does not have a .pdf extension; attempting to load anyway.", path)

    logger.info("Loading PDF: %s", path)
    try:
        loader = PyPDFLoader(str(path))
        documents = loader.load()
    except Exception as exc:  # noqa: BLE001 - we re-raise as a typed error below
        raise PDFLoadError(f"Failed to parse PDF '{path}': {exc}") from exc

    if not documents:
        raise PDFLoadError(f"PDF '{path}' loaded but contained zero pages.")

    total_chars = sum(len(doc.page_content) for doc in documents)
    logger.info(
        "Loaded %d page(s) from '%s' (%d characters total).",
        len(documents), path.name, total_chars,
    )
    return documents
