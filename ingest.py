#!/usr/bin/env python3
"""Ingest a medical encyclopedia PDF into Pinecone.

Usage:
    python ingest.py
    python ingest.py --pdf-path data/medical_book.pdf --index-name medical-encyclopedia
    python ingest.py --pdf-path data/sample_medical_book.pdf   # quick smoke test

Pipeline: load_pdf -> split_documents -> create_index -> upsert_documents.
See README.md > Running Ingestion for the full walkthrough.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from src.config import ConfigError, settings
from src.data_loader import PDFLoadError, PDFNotFoundError, load_pdf
from src.text_splitter import split_documents
from src.vector_store import PineconeAuthError, PineconeConnectionError, create_index, upsert_documents

logger = logging.getLogger("ingest")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--pdf-path",
        default=str(settings.default_pdf_path),
        help="Path to the source PDF (default: data/medical_book.pdf).",
    )
    parser.add_argument(
        "--index-name",
        default=settings.pinecone_index_name,
        help=f"Pinecone index name (default: {settings.pinecone_index_name}).",
    )
    parser.add_argument("--chunk-size", type=int, default=settings.chunk_size, help="Characters per chunk.")
    parser.add_argument("--chunk-overlap", type=int, default=settings.chunk_overlap, help="Overlap between chunks.")
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Chunks embedded/upserted per Pinecone batch."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging (e.g. full prompts, per-batch detail)."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    start = time.monotonic()
    logger.info("=== Medical AI Chatbot: ingestion ===")
    logger.info("PDF: %s | Index: %s", args.pdf_path, args.index_name)

    try:
        documents = load_pdf(args.pdf_path)
    except PDFNotFoundError as exc:
        logger.error(str(exc))
        return 1
    except PDFLoadError as exc:
        logger.error("Could not read the PDF: %s", exc)
        return 1

    chunks = split_documents(documents, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    if not chunks:
        logger.error("Splitting produced zero chunks; nothing to ingest. Is the PDF empty/scanned-image-only?")
        return 1

    try:
        create_index(index_name=args.index_name)
        upserted = upsert_documents(chunks, index_name=args.index_name, batch_size=args.batch_size)
    except ConfigError as exc:
        logger.error("Configuration problem: %s", exc)
        return 1
    except PineconeAuthError as exc:
        logger.error("Pinecone authentication failed: %s", exc)
        return 1
    except PineconeConnectionError as exc:
        logger.error("Pinecone connection problem: %s", exc)
        return 1

    elapsed = time.monotonic() - start
    logger.info(
        "Done. Ingested %d page(s) -> %d chunk(s) -> %d vector(s) into '%s' in %.1fs.",
        len(documents), len(chunks), upserted, args.index_name, elapsed,
    )
    logger.info("You can now run the app: python app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
