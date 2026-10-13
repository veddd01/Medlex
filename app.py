#!/usr/bin/env python3
"""Flask web application for the Medical AI Chatbot.

Routes:
    GET  /            Liveness probe / API entry point (JSON).
    GET  /health      Liveness/readiness probe (JSON).
    POST /ask         {"question": "..."} -> {"answer": "...", "sources": [...]}
    POST /ask/stream  SSE streaming simulated answer.
    POST /upload      Upload and ingest a PDF.
    POST /feedback    Record user feedback.
    GET  /history/<id> Get session chat history.

The RAG pipeline (embedding model + FLAN-T5 + Pinecone connection) is
initialized once at startup, not per-request — see `_initialize_pipeline`.
"""

from __future__ import annotations

import logging
import sys
import os
import json
import time
import uuid

from flask import Flask, jsonify, request, Response
from werkzeug.utils import secure_filename

from src import vector_store
from src.config import ConfigError, settings
from src.llm import GenerationError, LLMLoadError
from src.rag_pipeline import RAGPipeline
from src.vector_store import PineconeAuthError, PineconeConnectionError, VectorStoreError

from src.emergency import check_emergency, EMERGENCY_MESSAGE
from src.memory import memory, rewrite_with_context
from src.data_loader import load_pdf
from src.text_splitter import split_documents
from src.vector_store import upsert_documents
from src.reranker import rerank_chunks
from src.hybrid_search import hybrid_search
from src.rate_limiter import rate_limiter
from src.cache import response_cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app")

MAX_QUESTION_LENGTH = 1000  # generous upper bound; guards against abuse/huge payloads


def _initialize_pipeline() -> RAGPipeline:
    """Build the RAG pipeline, failing fast and loudly on bad configuration.

    - Missing env vars or a rejected API key -> log + exit (real
      misconfiguration; don't serve a broken app).
    - A transient Pinecone connectivity problem -> warn and continue; the
      server still starts, and /ask will surface the error per-request
      until connectivity returns.
    """
    try:
        settings.require_pinecone()
    except ConfigError as exc:
        logger.critical("Startup aborted: %s", exc)
        sys.exit(1)

    try:
        pipeline = RAGPipeline()
    except LLMLoadError as exc:
        logger.critical("Startup aborted: failed to load the LLM: %s", exc)
        sys.exit(1)

    try:
        vector_store.get_client().list_indexes()
    except PineconeAuthError as exc:
        logger.critical("Startup aborted: %s", exc)
        sys.exit(1)
    except PineconeConnectionError as exc:
        logger.warning(
            "Could not reach Pinecone at startup (%s). The server will start "
            "anyway, but /ask will return errors until this is resolved.", exc,
        )

    return pipeline


app = Flask(__name__)
rag_pipeline = _initialize_pipeline()


@app.route("/")
def index():
    """Liveness probe / API entry point."""
    return jsonify({
        "status": "ok",
        "service": "MedLex API",
        "llm_model": rag_pipeline.llm_model_name,
    })


@app.route("/health")
def health():
    """Liveness/readiness probe."""
    return jsonify({"status": "ok", "llm_model": rag_pipeline.llm_model_name})


@app.route("/ask", methods=["POST"])
@rate_limiter.limit()
def ask():
    """Answer a medical question, grounded in the ingested encyclopedia.

    Request body:  {"question": "What causes diabetes?"}
    Success (200): {"answer": "...", "sources": [{"page": 142, "score": 0.83, ...}]}
    Error (4xx/5xx): {"error": "human-readable message"}
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be JSON with a 'question' field."}), 400

    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "'question' must be a non-empty string."}), 400

    question = question.strip()
    if len(question) > MAX_QUESTION_LENGTH:
        return jsonify({"error": f"'question' must be under {MAX_QUESTION_LENGTH} characters."}), 400

    session_id = payload.get("session_id")
    history_provided = payload.get("history")

    # 1. Emergency detection
    emergency_text = check_emergency(question)
    if emergency_text:
        return jsonify({
            "answer": emergency_text,
            "sources": [],
            "grounded": False,
            "emergency": True
        }), 200
        
    # Check cache
    cached_response = response_cache.get(question)
    if cached_response and not history_provided and not session_id:
        return jsonify(cached_response), 200

    # 2. Context rewriting
    if history_provided and isinstance(history_provided, list):
        search_query = rewrite_with_context(question, history_provided)
    elif session_id:
        history = memory.get_history(session_id)
        search_query = rewrite_with_context(question, history)
    else:
        search_query = question

    try:
        # Pass rewritten query to pipeline
        result = rag_pipeline.answer(search_query)
        result["emergency"] = False
        
        # Cache response
        if not history_provided and not session_id:
            response_cache.set(question, result)
        
        # Save to memory
        if session_id:
            memory.add_interaction(session_id, question, result.get("answer", ""))
            
    except PineconeAuthError as exc:
        logger.error("Pinecone auth error while answering: %s", exc)
        return jsonify({"error": "Vector database authentication failed. Check server configuration."}), 500
    except PineconeConnectionError as exc:
        logger.error("Pinecone connection error while answering: %s", exc)
        return jsonify({"error": "Could not reach the vector database. Please try again shortly."}), 503
    except VectorStoreError as exc:
        logger.error("Vector store error while answering: %s", exc)
        return jsonify({"error": "A retrieval error occurred while searching the knowledge base."}), 500
    except (GenerationError, LLMLoadError) as exc:
        logger.error("LLM error while answering: %s", exc)
        return jsonify({"error": "The language model failed to generate an answer. Please try again."}), 500
    except Exception:  # noqa: BLE001 - last-resort safety net; never leak internals to the client
        logger.exception("Unexpected error while answering question.")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

    return jsonify(result), 200


@app.route("/ask/stream", methods=["POST"])
@rate_limiter.limit()
def ask_stream():
    """Answer question with SSE streaming simulation."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be JSON with a 'question' field."}), 400

    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "'question' must be a non-empty string."}), 400

    session_id = payload.get("session_id")
    history_provided = payload.get("history")

    emergency_text = check_emergency(question)
    if emergency_text:
        def emergency_stream():
            words = emergency_text.split()
            for word in words:
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                time.sleep(0.05)
            yield f"data: {json.dumps({'done': True, 'sources': [], 'emergency': True})}\n\n"
        return Response(emergency_stream(), mimetype="text/event-stream")

    if history_provided and isinstance(history_provided, list):
        search_query = rewrite_with_context(question, history_provided)
    elif session_id:
        history = memory.get_history(session_id)
        search_query = rewrite_with_context(question, history)
    else:
        search_query = question

    try:
        result = rag_pipeline.answer(search_query)
        if session_id:
            memory.add_interaction(session_id, question, result.get("answer", ""))
            
        def generate_stream():
            answer = result.get("answer", "")
            words = answer.split()
            for word in words:
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                time.sleep(0.05)
            yield f"data: {json.dumps({'done': True, 'sources': result.get('sources', []), 'emergency': False})}\n\n"
            
        return Response(generate_stream(), mimetype="text/event-stream")
    except Exception as exc:
        logger.error("Error in ask_stream: %s", exc)
        return jsonify({"error": "Failed to stream answer."}), 500


@app.route("/feedback", methods=["POST"])
def feedback():
    """Record user feedback (thumbs up/down)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be JSON."}), 400

    required_fields = ["question", "answer", "rating", "session_id"]
    if not all(field in payload for field in required_fields):
        return jsonify({"error": "Missing required fields."}), 400

    feedback_file = os.path.join("data", "feedback.jsonl")
    os.makedirs("data", exist_ok=True)
    with open(feedback_file, "a") as f:
        json.dump(payload, f)
        f.write("\n")

    return jsonify({"status": "recorded"})


@app.route("/history/<session_id>", methods=["GET"])
def get_history(session_id):
    """Get chat history for a session."""
    history = memory.get_history(session_id)
    return jsonify({"session_id": session_id, "history": history})


@app.route("/upload", methods=["POST"])
def upload_pdf():
    """Upload and ingest a new PDF into the knowledge base."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
        
    if file and file.filename.endswith(".pdf"):
        filename = secure_filename(file.filename)
        upload_dir = os.path.join("data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        try:
            # Run ingestion logic
            documents = load_pdf(filepath)
            chunks = split_documents(documents, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
            upserted = upsert_documents(chunks, index_name=settings.pinecone_index_name, batch_size=100)
            return jsonify({
                "status": "ingested", 
                "chunks": len(chunks), 
                "upserted": upserted,
                "filename": filename
            })
        except Exception as exc:
            logger.error("Ingestion failed for %s: %s", filename, exc)
            return jsonify({"error": f"Ingestion failed: {str(exc)}"}), 500
            
    return jsonify({"error": "Invalid file type. Only PDF is allowed."}), 400


if __name__ == "__main__":
    import os
    # For production, prefer: gunicorn -w 2 -b 127.0.0.1:5000 app:app
    # (see README.md > Deployment). Use FLASK_DEBUG=1 for local development only.
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)
