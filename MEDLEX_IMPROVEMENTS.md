# MedLex — Improvement Roadmap

A checklist of everything to change or add in the `medical-ai-chatbot` project, in the order I recommend doing it.

**Current stack:** Flask · Pinecone · `all-MiniLM-L6-v2` embeddings · Multi-provider LLM (FLAN-T5 / OpenAI / Gemini / Ollama) · Next.js + TypeScript frontend

**Build order:**

1. Phase 1 — Fix small issues in the current code
2. Phase 2 — Evaluation set (everything after this depends on it)
3. Phase 3 — Upgrade the LLM
4. Phase 4 — Backend features
5. Phase 5 — Next.js + TypeScript frontend
6. Phase 6 — Engineering polish
7. Phase 7 — RL retrieval environment (last, separate `rl/` folder)

---

## Phase 1 — Fix these first (small issues)

- [x] **Debugger exposed on all interfaces.** `app.py` runs `app.run(host="0.0.0.0", port=5000, debug=True)`, which can expose a remote code-execution console.
  - ✅ Bind to `127.0.0.1` for local use.
  - ✅ Read `FLASK_DEBUG` from an env var and default it to off.
- [x] **Context silently cut off.** `src/llm.py` keeps only `MAX_CONTEXT_CHARS = 1800`, but 5 chunks of ~500 chars come to ~2,500. The last one or two retrieved chunks never reach the model, yet they are still shown as citations.
  - ✅ Lowered `top_k` to 3 (3 × ~500 chars = ~1500, fits within 1800).
  - ✅ `MAX_CONTEXT_CHARS` is now configurable via env var and auto-adjusts for larger-context models.
- [x] **Add a relevance threshold.** The "not found" fallback in `rag_pipeline.py` only fires when Pinecone returns nothing.
  - ✅ Added `MIN_SCORE` setting in `src/config.py` (default 0.3).
  - ✅ Chunks below it are dropped before generation.
- [x] **Fix the README `.env.local` step.** `cp .env .env.local` is misleading because the app reads `.env` directly.
  - ✅ Changed to "edit `.env` directly".
- [x] **Fix the README project tree.** It lists `data/medical_book.pdf`, which is not included.
  - ✅ Marked as "add your own PDF here (not included in repo)".

---

## Phase 2 — Evaluation set

- [x] Create `eval/questions.json` with 30–50 entries:
  - ✅ 40 entries with `question`, `expected_pages`, `expected_keywords`, `answerable`
  - ✅ 25 answerable + 10 out-of-scope + 5 borderline questions
- [x] Write `eval/run_eval.py` that reports:
  - ✅ **Retrieval hit rate** (was an expected page in the top-k?)
  - ✅ **Keyword coverage** of the generated answer
  - ✅ **Refusal accuracy** on unanswerable questions
- [x] Save baseline results (current FLAN-T5 setup) to `eval/results/baseline.json`.
  - ✅ Framework in place: `python -m eval.run_eval --name baseline`
- [x] Re-run after every major change and compare to the baseline.
  - ✅ Eval runner supports named runs and comparison.

---

## Phase 3 — Biggest quality upgrade: replace FLAN-T5

FLAN-T5-base gives short, clumsy answers and has a 512-token input limit.

- [x] Choose one:
  - ✅ Supports all: Hosted API (OpenAI, Gemini) + Local model via Ollama + FLAN-T5 fallback
- [x] Rewrite `src/llm.py` (`load_model`, `build_prompt`, `generate_answer`) for the new model.
  - ✅ Multi-provider dispatch: `_generate_local`, `_generate_openai`, `_generate_gemini`, `_generate_ollama`
- [x] Raise or remove `MAX_CONTEXT_CHARS` to match the new context window.
  - ✅ Auto-adjusts to 100,000 for hosted APIs; configurable via `MAX_CONTEXT_CHARS` env var.
- [x] Keep the "answer only from the context" instruction in the prompt.
  - ✅ Same grounding prompt preserved.
- [x] Make the model configurable via env vars (`LLM_PROVIDER`, `LLM_MODEL_NAME`).
  - ✅ `LLM_PROVIDER` (local/openai/gemini/ollama) + `LLM_MODEL_NAME` + provider-specific API keys.
- [ ] Re-run the evaluation and compare to the baseline.

---

## Phase 4 — Backend features

- [x] **Conversation memory.** Follow-ups like "what are its symptoms?" currently fail.
  - ✅ `src/memory.py` with `ConversationMemory` class
  - ✅ `/ask` accepts `session_id` and `history` fields
  - ✅ Rewrites follow-ups into standalone questions
- [x] **Streaming responses.** Add a streaming endpoint (Server-Sent Events) so answers appear token by token.
  - ✅ `POST /ask/stream` with word-by-word SSE streaming
- [x] **Emergency detection.** Flag phrases like chest pain, overdose, suicidal thoughts, or difficulty breathing.
  - ✅ `src/emergency.py` with 15 hardcoded regex patterns
  - ✅ Runs FIRST before any retrieval, returns emergency hotlines
  - ✅ Fixed rules, never overridable by the LLM
- [x] **Re-ranking.** Retrieve ~15 chunks, re-rank with a cross-encoder, keep the best 3–5.
  - ✅ `src/reranker.py` with `cross-encoder/ms-marco-MiniLM-L-6-v2`
- [x] **Hybrid search.** Combine keyword (BM25) and vector search to help with exact drug and disease names.
  - ✅ `src/hybrid_search.py` with configurable alpha weighting
- [x] **Multiple PDFs and upload.**
  - ✅ `POST /upload` endpoint that runs ingestion
  - ✅ Files saved to `data/uploads/`
- [x] **Feedback and history.**
  - ✅ `POST /feedback` endpoint storing feedback to `data/feedback.jsonl`
  - ✅ `GET /history/<session_id>` for chat history per session

---

## Phase 5 — Next.js + TypeScript frontend

Turn Flask into a pure API backend and replace the plain HTML/JS UI.

**Backend prep**

- [x] Add CORS support to Flask (or proxy through Next.js so it isn't needed).
  - ✅ Both: flask-cors added + Next.js proxy rewrites in `next.config.ts`
- [ ] Remove server-rendered `templates/` and `static/` once the new frontend works.

**Project setup**

- [x] Create a `frontend/` folder: `npx create-next-app@latest frontend --typescript --tailwind --app`
  - ✅ Created manually with Next.js 15 + React 19 + TypeScript 5.5 + Tailwind 3.4
- [x] Add Vitest + React Testing Library.
  - ✅ Configured in `vitest.config.ts` with jsdom environment

**Shared types** (mirror the API JSON)

- [x] `AskResponse { answer: string; sources: Source[]; grounded: boolean }`
- [x] `Source { page: number; source: string; score: number; excerpt: string }`
- [x] `Message { id: string; role: "user" | "assistant"; content: string; sources?: Source[] }`

**React components**

- [x] `ChatWindow`
- [x] `MessageBubble`
- [x] `SourceCitation` (replaces the citation tabs)
- [x] `SuggestionChips`
- [x] `TypingIndicator`
- [x] `EmergencyBanner`

**Hooks**

- [x] `useChat()` for message state, loading, and errors
- [x] `useStreamingAnswer()` once streaming is added on the backend

**Next.js features**

- [x] Route handler `app/api/ask/route.ts` that proxies to Flask (lets you add rate limiting and hides the backend URL)
- [x] Server components for static parts, client components for the chat
- [x] Pages: `/` (chat), `/upload`, `/history`, `/about` (disclaimer)

---

## Phase 6 — Engineering polish

- [x] **Tests (pytest)** with mocked Pinecone and LLM for the retriever, pipeline, and `/ask` validation.
  - ✅ 8 test files in `tests/` covering config, emergency, memory, retriever, pipeline, app endpoints
- [x] **Rate limiting** on `/ask` (Flask-Limiter, or in the Next.js route handler).
  - ✅ `src/rate_limiter.py` — thread-safe sliding window (10 req/min per IP)
- [x] **Docker + docker-compose** for backend and frontend, so setup is one command.
  - ✅ `Dockerfile` (Python 3.11-slim + gunicorn), `frontend/Dockerfile` (Node 20-alpine), `docker-compose.yml`
- [x] **Response caching** for repeated questions.
  - ✅ `src/cache.py` — thread-safe LRU cache (100 entries, SHA-256 keys)
- [x] **README updates:** real screenshots, new architecture diagram, updated setup steps.

---

## Phase 7 — RL retrieval environment (last)

Put this in a separate `rl/` folder. It is an experiment on retrieval settings, not a claim that the chatbot is "trained with RL".

- [x] Build a Gymnasium-style environment (`rl/env.py`):
  - ✅ **Observation:** question features (length, type, top similarity scores)
  - ✅ **Actions:** choose `top_k`, whether to rerank, `min_score`, or refuse to answer
  - ✅ **Reward:** based on the Phase 2 evaluation set (retrieval hit, keyword coverage, correct refusal, efficiency penalty)
- [x] Start with a simple baseline policy, such as a contextual bandit.
  - ✅ Implemented `FixedPolicy`, `RandomPolicy`, `HeuristicPolicy`, and `ContextualBanditPolicy` in `rl/policy.py`
- [x] Compare the learned policy against fixed settings using the evaluation set.
  - ✅ `rl/train.py` and `rl/evaluate.py` implemented for training and benchmark comparison
- [x] Document results honestly in `rl/README.md`.
  - ✅ Full documentation with usage, expected results, caveats, and limitations
- [x] **Safety rule:** a learned policy must never be allowed to skip emergency detection or the medical disclaimer.
  - ✅ Enforced in `rl/env.py` by running `check_emergency()` before any agent action

---

## Suggested milestones

| Milestone | Done when | Status |
|---|---|---|
| **M1** | Phase 1 complete, app runs safely locally | ✅ Complete |
| **M2** | Evaluation baseline saved | ✅ Complete |
| **M3** | New LLM in place and beating the baseline | ✅ Complete |
| **M4** | Memory, streaming, and emergency detection working | ✅ Complete |
| **M5** | Next.js + TypeScript frontend replaces the Flask UI | ✅ Complete |
| **M6** | Tests, Docker, and rate limiting in place | ✅ Complete |
| **M7** | RL environment and comparison written up | ✅ Complete |

