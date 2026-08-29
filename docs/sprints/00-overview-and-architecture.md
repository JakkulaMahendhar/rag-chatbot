# RAG Chatbot — Complete Application Overview

## What this project actually is

A **Retrieval-Augmented Generation (RAG)** system: users upload their own
documents (PDF/DOCX/TXT), the system extracts and indexes the text, and
users can then ask natural-language questions that get answered **using
only their own uploaded content** — not the LLM's general training
knowledge.

## The example used in every file in this folder

> **Sarah**, an employee at **Acme Corp**, uploads `Employee_Leave_Policy.pdf`.
> Its Section 2 says: *"All full-time employees are entitled to 12 paid
> sick leaves per calendar year, accrued monthly at 1 leave per month."*
> Sarah then asks the chatbot: **"How many sick leaves do I get per
> year?"**

Gemini, the LLM this project uses, has never seen Acme Corp's internal HR
policy — that document was never part of its training data. Pasting the
whole document into every prompt would also be slow and eventually hit
context-length limits once a company has hundreds of documents. RAG solves
this by finding *only the one relevant paragraph* out of the whole document
set, and handing *just that paragraph* to the LLM alongside Sarah's
question.

## The complete pipeline, end to end

```
                    ┌─────────────┐
                    │   Browser    │  Sarah's chat + upload UI (Sprint 13)
                    └──────┬──────┘
                           │ HTTPS / JSON
                           ▼
                    ┌─────────────┐
                    │   FastAPI    │  app/main.py
                    │   Web App    │
                    └──────┬──────┘
             ┌─────────────┼─────────────────┐
             ▼             ▼                 ▼
      ┌───────────┐  ┌───────────┐   ┌──────────────┐
      │ PostgreSQL │  │  Worker    │   │  Gemini API   │
      │ (Sarah's   │  │  Process   │   │  (generates    │
      │ account +  │  │(Sprint 12) │   │  the answer)   │
      │ document)  │  └─────┬──────┘   └──────────────┘
      └───────────┘        │ parses, chunks, embeds
                            ▼          Sarah's PDF
                    ┌───────────────┐
                    │ ChromaDB      │  stores the sick-leave
                    │ Server        │  sentence as a vector
                    └───────────────┘
                            │
                    ┌───────────────┐
                    │ BM25 Index    │  also indexes it by
                    │ (keyword)     │  exact keyword ("sick leaves")
                    └───────────────┘
```

## Why each major building block was chosen, and what it's for

| Class / library / service | What it does | Why we used it | How it compares to the obvious alternative |
|---|---|---|---|
| **FastAPI** | Receives Sarah's upload and chat requests over HTTP | Async-native (doesn't block while Gemini or ChromaDB responds), automatic request validation via Pydantic, built-in OpenAPI docs | Flask is simpler but synchronous by default — every waiting network call (Gemini, Chroma) would block the whole server; FastAPI keeps handling other users' requests while Sarah's is waiting |
| **PostgreSQL** | Stores Sarah's account and her document's status/filename | Relational data with real ownership relationships ("this document belongs to this user") and ACID guarantees | A plain file or NoSQL store would need to reinvent relational integrity by hand for something Postgres already does correctly |
| **ChromaDB** | Stores the sick-leave sentence as a vector, finds it again by meaning | Purpose-built for fast nearest-neighbor vector search, which Postgres doesn't do natively | Storing vectors as Postgres columns and comparing them in Python would work for a handful of chunks, but has no real index — it gets slow fast as documents pile up |
| **A separate background worker** | Actually parses, chunks, and embeds Sarah's PDF | Keeps the upload request itself fast (it just saves the file and returns), so the browser never sits on a 30–40 second HTTP call | Doing the heavy work inside the same request that receives the upload risks the request timing out on a slow connection or a large PDF |
| **JWT tokens** | Prove every request claiming to be Sarah actually is Sarah | Stateless — the frontend and backend are two separate deployments, so a token that's self-verifying (no shared session store) is the natural fit | Server-side session cookies would need both services to share session state, which adds infrastructure for no real benefit here |
| **Docker Compose (local) / Docker (production)** | Runs Postgres, ChromaDB, the web app, and the worker as the same containers everywhere | Local testing behaves the same way production does, so a bug like "the worker and web app fighting over the same ChromaDB file" (see Sprint 12) shows up on a laptop, not for a real user | Running the app with `uvicorn --reload` on bare metal locally, then something different in production, hides exactly this kind of bug until it's live |

## Technology stack (verified against `requirements.txt` / `package.json`)

### Backend
| Library | Version | Purpose |
|---|---|---|
| FastAPI | 0.139.0 | Web framework, API routing, request validation |
| Uvicorn | 0.51.0 | ASGI server that runs FastAPI |
| Pydantic | 2.13.4 | Data validation, settings management |
| SQLAlchemy | 2.0.51 | ORM — Python objects ↔ Postgres rows, async |
| asyncpg | 0.31.0 | Async Postgres driver (web app) |
| psycopg2-binary | 2.9.12 | Sync Postgres driver (Alembic migrations) |
| Alembic | 1.18.5 | Database schema migrations |
| ChromaDB | 1.5.9 | Vector database |
| sentence-transformers | 5.6.0 | Generates embeddings |
| torch | 2.13.0 | ML tensor library underneath sentence-transformers |
| transformers | 5.13.1 | Hugging Face model loading |
| rank-bm25 | 0.2.2 | Keyword search algorithm (BM25) |
| langchain-text-splitters | 1.1.2 | Splits documents into chunks |
| PyMuPDF (fitz) | 1.28.0 | Extracts text from PDF files |
| python-docx | 1.2.0 | Extracts text from Word files |
| google-generativeai | 0.8.6 | Gemini LLM client |
| ollama | 0.6.2 | Ollama LLM client (local-model alternative) |
| passlib + bcrypt | 1.7.4 / 4.1.3 | Password hashing |
| python-jose | 3.5.0 | JWT creation/verification |
| pytest + pytest-asyncio | 9.1.1 / 1.4.0 | Testing |

### Frontend
| Library | Purpose |
|---|---|
| Next.js 16 (App Router, Turbopack) | React framework, routing, build tooling |
| TypeScript | Type safety |
| Tailwind CSS v4 | Styling |
| shadcn/ui (Base UI primitives) | Accessible UI components |
| TanStack Query | Server-state fetching/caching/polling |
| React Hook Form + Zod | Form handling and validation |
| next-themes | Light/dark/system theme switching |

### Infrastructure
| Tool | Purpose |
|---|---|
| Docker + Docker Compose | Local dev matching production, multi-service orchestration |
| GitHub Actions | CI — runs tests automatically on every push |
| Render | Cloud hosting (web app, worker, database, static frontend) |

## The AI/ML models actually used

| Model | Used for | Where |
|---|---|---|
| `all-MiniLM-L6-v2` | Turns text (like the sick-leave sentence) into a 384-number vector | `app/core/ai_registry.py` |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Re-scores retrieved chunks for true relevance to Sarah's question | `app/services/reranker.py` |
| `gemini-2.5-flash` | Writes the final answer to Sarah | `app/services/llm/gemini.py` |
| `llama3.1` (via Ollama, configurable) | Local alternative to Gemini, no API cost | `app/services/llm/ollama.py` |

## How to read the rest of this documentation

Each file covers one phase of development, in the order it was actually
built. Each one explains, using Sarah's example at that exact step:
**what class or library was used, what it does, why it was chosen over the
obvious alternative, and how the flow works concretely.**

See [14-bugs-and-lessons-learned.md](14-bugs-and-lessons-learned.md) for a
consolidated list of every real bug found while building this, and exactly
how each one was fixed.
