# RAG Chatbot — Complete Application Overview

## What this project actually is

A production-style **Retrieval-Augmented Generation (RAG)** system: users upload
their own documents (PDF/DOCX/TXT), the system extracts and indexes the text,
and users can then ask natural-language questions that get answered **using
only their own uploaded content** — not the LLM's general training knowledge.

Real example of the core problem this solves:

> Gemini (the LLM this project uses) has no idea what's in your company's
> internal HR policy document, because that document was never part of its
> training data, and even if you pasted the whole document into a prompt every
> time, it would be slow, expensive, and hit context-length limits fast for
> large document sets. RAG solves this by: finding *only the relevant
> paragraphs* from your documents for a given question, and feeding *just
> those paragraphs* to the LLM alongside the question.

## The complete pipeline, end to end

```
                    ┌─────────────┐
                    │   Browser    │  (Next.js frontend, Sprint "Frontend")
                    └──────┬──────┘
                           │ HTTPS / JSON
                           ▼
                    ┌─────────────┐
                    │   FastAPI    │  (app/main.py)
                    │   Web App    │
                    └──────┬──────┘
             ┌─────────────┼─────────────────┐
             ▼             ▼                 ▼
      ┌───────────┐  ┌───────────┐   ┌──────────────┐
      │ PostgreSQL │  │  Worker    │   │  Gemini API   │
      │ (users,    │  │  Process   │   │  (LLM calls)  │
      │ documents) │  │(Sprint 12) │   └──────────────┘
      └───────────┘  └─────┬──────┘
                            │ writes vectors
                            ▼
                    ┌───────────────┐
                    │ ChromaDB      │  (Sprint 6, later
                    │ Server        │   moved to its own
                    │ (vectors)     │   server, Sprint 12)
                    └───────────────┘
                            │
                    ┌───────────────┐
                    │ BM25 Index    │  (keyword search,
                    │ (local files) │   Sprint 9)
                    └───────────────┘
```

## Why it was built this way — the core engineering decisions

| Decision | Why |
|---|---|
| **Hybrid search** (vector + keyword), not just vector search | Pure vector (semantic) search misses exact keyword matches sometimes (e.g. product codes, names). Pure keyword search misses paraphrased questions. Combining both (Sprint 9) covers more real questions correctly. |
| **Separate background worker for document processing** | Uploading and processing a document (parsing, chunking, embedding — can take 40+ seconds for large files) inside one HTTP request risks timeouts and blocks the server. Sprint 12 split this into "accept fast, process in background." |
| **PostgreSQL for structured data, ChromaDB for vectors** | These are fundamentally different data shapes. Postgres is excellent at relational data (who owns what, status tracking) with ACID guarantees. ChromaDB is purpose-built for fast approximate-nearest-neighbor vector search, which Postgres isn't (without extensions). Using the right tool for each job. |
| **JWT auth, not session cookies** | The frontend and backend are genuinely separate applications (different deploy targets, different hosts) — a stateless bearer token is the standard, simplest fit for that shape, versus server-side session state that would need sticky infrastructure. |
| **Docker Compose for local dev, matching what's deployed** | "Works on my machine" bugs happen when local dev doesn't match production. Running the exact same containers locally that get deployed (Sprint 11) catches integration bugs (like the ChromaDB race condition, see Sprint 12/bugs doc) *before* they hit production. |

## Technology stack (verified against `requirements.txt` / `package.json`)

### Backend
| Library | Version | Purpose |
|---|---|---|
| FastAPI | 0.139.0 | Web framework, API routing, request validation |
| Uvicorn | 0.51.0 | ASGI server that actually runs FastAPI |
| Pydantic | 2.13.4 | Data validation, settings management |
| SQLAlchemy | 2.0.51 | ORM — Python objects ↔ Postgres rows, async |
| asyncpg | 0.31.0 | Async Postgres driver (used by the web app) |
| psycopg2-binary | 2.9.12 | Sync Postgres driver (used by Alembic migrations) |
| Alembic | 1.18.5 | Database schema migrations (version-controlled schema changes) |
| ChromaDB | 1.5.9 | Vector database — stores embeddings, does similarity search |
| sentence-transformers | 5.6.0 | Generates embeddings (turns text into vectors) |
| torch | 2.13.0 | The actual ML tensor library underneath sentence-transformers |
| transformers | 5.13.1 | Hugging Face model loading (used by sentence-transformers + reranker) |
| rank-bm25 | 0.2.2 | Keyword search algorithm (BM25) |
| langchain-text-splitters | 1.1.2 | Splits long documents into smaller chunks intelligently |
| PyMuPDF (fitz) | 1.28.0 | Extracts text from PDF files |
| python-docx | 1.2.0 | Extracts text from Word (.docx) files |
| google-generativeai | 0.8.6 | Gemini LLM client |
| ollama | 0.6.2 | Ollama LLM client (local-model alternative to Gemini) |
| passlib + bcrypt | 1.7.4 / 4.1.3 | Password hashing |
| python-jose | 3.5.0 | JWT token creation/verification |
| pytest + pytest-asyncio | 9.1.1 / 1.4.0 | Testing |

### Frontend
| Library | Purpose |
|---|---|
| Next.js 16 (App Router, Turbopack) | React framework, routing, build tooling |
| TypeScript | Type safety |
| Tailwind CSS v4 | Styling |
| shadcn/ui (Base UI primitives) | Accessible UI component library |
| TanStack Query | Server-state management (API data fetching/caching/polling) |
| React Hook Form + Zod | Form handling and validation |
| next-themes | Light/dark/system theme switching |

### Infrastructure
| Tool | Purpose |
|---|---|
| Docker + Docker Compose | Local dev matching production, multi-service orchestration |
| GitHub Actions | CI — runs tests automatically on every push |
| Render | Cloud hosting (web app, worker, database, static frontend) |

## The AI/ML models actually used (real model names, not generic labels)

| Model | Used for | Where |
|---|---|---|
| `all-MiniLM-L6-v2` | Turning text into 384-dimension embedding vectors | `app/core/ai_registry.py`, every chunk and every search query |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Re-scoring retrieved chunks for relevance (reranking) | `app/services/reranker.py` |
| `gemini-2.5-flash` | Generating the final natural-language answer | `app/services/llm/gemini.py` |
| (configurable) e.g. `llama3.1` via Ollama | Alternative to Gemini, runs locally, no API cost | `app/services/llm/ollama.py` |

## How to read the rest of this documentation

Each file in `docs/sprints/` covers one phase of development, in the order it
was actually built, matching the git commit history and the README's own
sprint numbering. Each file includes:

- **What we built** — the actual feature, with real file paths
- **Why we built it this way** — the reasoning, alternatives considered
- **How it works** — a concrete example walked through step by step
- **What works well** (positive scenarios) — verified, not assumed
- **What doesn't / limitations** (negative scenarios) — honest gaps, edge
  cases, and real bugs found during development, not hidden

See `14-bugs-and-lessons-learned.md` for a consolidated list of every real,
reproduced bug found during this project and exactly how it was diagnosed
and fixed — this is often the most instructive file for understanding how
the system actually behaves under real conditions, not just the happy path.
