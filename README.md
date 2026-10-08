# MedLex — Medical AI RAG Chatbot

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![RAG](https://img.shields.io/badge/Architecture-RAG-6E56CF)](#architecture)

> **Repository status:** documentation is being prepared first. The application source code has **not** been pushed to this GitHub repository yet.

MedLex is a Retrieval-Augmented Generation (RAG) medical-reference chatbot designed to answer questions from a medical encyclopedia supplied by the user. The system retrieves relevant evidence first, re-ranks it, and then asks an LLM to generate a grounded response from that retrieved context.

**MedLex is an educational/engineering project, not a medical device or a substitute for professional medical advice.**

## What MedLex Does

A typical query follows this pipeline:

1. The user's question is checked for emergency phrases.
2. Conversation history can be used to rewrite follow-up questions.
3. Relevant passages are retrieved from Pinecone using vector search.
4. BM25 keyword matching is combined with the vector results.
5. A cross-encoder re-ranks the candidate passages.
6. The best passages are supplied to the selected LLM as grounded context.
7. The response is returned with source metadata and excerpts.
8. If retrieval is empty or below the configured relevance threshold, MedLex returns a fixed fallback rather than asking the model to guess.

## Key Features

- **Grounded RAG:** generation is constrained to retrieved medical-reference context.
- **Hybrid retrieval:** dense embeddings + BM25 keyword search.
- **Cross-encoder re-ranking:** improves the ordering of retrieved passages.
- **Multi-provider LLM layer:** local FLAN-T5, OpenAI, Gemini, and Ollama.
- **Source citations:** page, source file, score, and excerpt are returned with answers.
- **Safety-first routing:** emergency detection runs before retrieval and LLM generation.
- **Conversation memory:** supports session-based history and follow-up rewriting.
- **Streaming:** Server-Sent Events endpoint for streamed responses.
- **PDF ingestion:** upload or ingest additional medical documents into the knowledge base.
- **Engineering controls:** tests, rate limiting, LRU caching, Docker, Docker Compose, and an evaluation harness.

## Architecture

~~~mermaid
flowchart LR
    A[Medical PDF] --> B[PDF Loader]
    B --> C[Recursive Text Splitter]
    C --> D[Hugging Face Embeddings]
    D --> E[(Pinecone)]

    Q[User Question] --> S{Emergency Check}
    S -->|Emergency| X[Configured Emergency Guidance]
    S -->|Normal| R[Vector Retrieval]
    R --> H[BM25 + Vector Hybrid Search]
    H --> K[Cross-Encoder Re-ranking]
    K --> L[Top Relevant Chunks]
    L --> G[LLM]
    Q --> G
    G --> O[Answer + Sources]
~~~

### Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Gunicorn |
| RAG | LangChain, PyPDF, custom retrieval pipeline |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector database | Pinecone Serverless |
| Keyword search | BM25 |
| Re-ranker | ms-marco-MiniLM-L-6-v2 |
| LLMs | FLAN-T5, OpenAI, Gemini, Ollama |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Testing | Pytest, Vitest / React Testing Library |
| Deployment | Docker, Docker Compose |

## Project Structure

The structure below reflects the application currently developed locally. The GitHub repository is intentionally **README-only for now**.

~~~text
Medlex/
├── app.py
├── ingest.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── MEDLEX_IMPROVEMENTS.md
├── data/
├── eval/
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── text_splitter.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retriever.py
│   ├── hybrid_search.py
│   ├── reranker.py
│   ├── rag_pipeline.py
│   ├── llm.py
│   ├── memory.py
│   ├── emergency.py
│   ├── rate_limiter.py
│   └── cache.py
├── tests/
└── frontend/
    ├── package.json
    └── src/
        ├── app/
        ├── components/
        ├── hooks/
        └── types/
~~~

## Setup

### 1. Clone the repository

~~~bash
git clone https://github.com/veddd01/Medlex.git
cd Medlex
~~~

> The repository currently contains documentation only. Add the application source before attempting to run the commands below.

### 2. Python environment

~~~bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
~~~

On Windows:

~~~text
venv\Scripts\activate
~~~

### 3. Environment variables

Create a local .env file and configure the services you plan to use.

~~~ini
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
PINECONE_CLOUD=aws

EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

LLM_PROVIDER=local
LLM_MODEL_NAME=google/flan-t5-base

OPENAI_API_KEY=
GEMINI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

MAX_CONTEXT_CHARS=1800
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K=3
MIN_SCORE=0.3
~~~

Supported LLM providers:

- **local** — FLAN-T5 through Hugging Face Transformers
- **openai** — OpenAI API
- **gemini** — Google Gemini API
- **ollama** — locally hosted Ollama models

### 4. Ingest medical documents

~~~bash
python ingest.py --pdf-path data/medical_book.pdf
~~~

For the bundled sample document:

~~~bash
python ingest.py --pdf-path data/sample_medical_book.pdf --index-name medlex-sample
~~~

## Running the Application

### Docker

~~~bash
docker-compose up --build
~~~

The backend runs on port **5000** and the Next.js frontend on port **3000**.

### Manual

Backend:

~~~bash
python app.py
~~~

Frontend:

~~~bash
cd frontend
npm install
npm run dev
~~~

Then open:

- Frontend: http://localhost:3000
- Backend: http://127.0.0.1:5000

## API

| Endpoint | Method | Purpose |
|---|---|---|
| /ask | POST | Grounded question answering |
| /ask/stream | POST | SSE streaming response |
| /upload | POST | PDF upload and ingestion |
| /feedback | POST | Store answer feedback |
| /history/<session_id> | GET | Retrieve conversation history |
| /health | GET | Health/readiness check |

Example request:

~~~bash
curl -X POST http://127.0.0.1:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What causes diabetes?","session_id":"demo-session"}'
~~~

Example response shape:

~~~json
{
  "answer": "...",
  "sources": [
    {
      "page": 4,
      "source": "medical_book.pdf",
      "score": 0.91,
      "excerpt": "..."
    }
  ],
  "grounded": true,
  "emergency": false
}
~~~

## Evaluation

MedLex includes an evaluation set and runner for retrieval and answer-quality checks.

~~~bash
python -m eval.run_eval --name baseline --verbose
~~~

The evaluation framework measures:

- retrieval hit rate
- keyword coverage
- refusal accuracy for unanswerable questions

The current evaluation setup contains **40 questions** covering answerable, out-of-scope, and borderline cases.

## Testing

~~~bash
pytest tests/ -v
~~~

The test suite includes configuration, retrieval, RAG pipeline, emergency detection, memory, and API endpoint coverage using mocked external services where appropriate.

Frontend tests can be run with:

~~~bash
cd frontend
npm test
~~~

## Safety & Guardrails

MedLex is intentionally designed so that safety checks are not delegated to the LLM.

**Emergency detection** runs before retrieval and generation. Configured emergency patterns can immediately route the request to the project's emergency guidance.

**Low-confidence retrieval** is handled deterministically. If no relevant passages are found or scores fall below MIN_SCORE, the pipeline returns a fixed "not found in the encyclopedia" response instead of generating an unsupported medical answer.

The project also exposes source excerpts so users can inspect the evidence that grounded a response.

## Future Work

- Gymnasium-style RL environment for retrieval-policy experiments
- Admin controls for re-ingestion and index management
- Expanded multilingual support
- Further evaluation against stronger LLM providers
- Additional observability and production deployment tooling

## Disclaimer

MedLex is not a medical device and is not reviewed or validated by clinicians. Retrieval and generation can be incomplete, incorrect, or misleading. It should not be used for diagnosis, treatment decisions, or emergency care.

For urgent or potentially serious medical situations, seek qualified professional or emergency medical assistance rather than relying on this application.

---

Built as an engineering project exploring **RAG, retrieval quality, grounding, LLM orchestration, and safety-aware AI systems**.
