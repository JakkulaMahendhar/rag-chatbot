# 🤖 RAG Chatbot - Retrieval Augmented Generation AI System

A production-style **Retrieval Augmented Generation (RAG) chatbot** built from scratch using **Python, FastAPI, Sentence Transformers, and Vector Database technologies**.

This project demonstrates how modern AI applications are engineered:

```text
Documents
    |
    ↓
Text Extraction
    |
    ↓
Intelligent Chunking
    |
    ↓
Embedding Generation
    |
    ↓
Vector Database
    |
    ↓
Semantic Search
    |
    ↓
LLM Response Generation
```

The objective is to build a complete enterprise-grade AI knowledge assistant similar to systems used for:

- Internal company knowledge search
- Document intelligence platforms
- AI assistants
- Customer support automation

---

# ⚡ Getting Started

Everything you need to clone this repo and have it running locally —
backend, frontend, database, vector store, and worker — with exact
commands. This is the current, accurate setup guide; treat the
sprint-by-sprint sections further down as history, not instructions.

## Prerequisites

| Tool | Needed for | Get it |
|---|---|---|
| **Git** | Cloning the repo | — |
| **Docker Desktop** | Running Postgres + ChromaDB + backend + worker with one command (recommended path) | https://www.docker.com/products/docker-desktop |
| **Python 3.11+** | Only if running the backend *outside* Docker | https://www.python.org/downloads |
| **Node.js 20+ and npm** | The frontend | https://nodejs.org |
| **Ollama** (optional) | The default local LLM — skip this if you'll use Gemini instead | https://ollama.com |

## 1. Clone the repository

```bash
git clone <repository-url>
cd rag-chatbot
```

## 2. Configure environment variables

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

Then open `.env` and fill in what's actually required — everything else
already has a sensible default (see the full comments in `.env.example`):

| Variable | Required? | What it's for |
|---|---|---|
| `JWT_SECRET_KEY` | **Yes** | Generate one: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` / `DATABASE_URL_SYNC` | No, if using Docker Compose | The default values already match the `db` service below |
| `LLM_PROVIDER` | No | Defaults to `ollama` (local, free). Set to `gemini` to use Google's API instead |
| `GEMINI_API_KEY` | Only if `LLM_PROVIDER=gemini` | Free key at https://aistudio.google.com/apikey — free tier is capped at 20 requests/day |

`frontend/.env.local` only needs `NEXT_PUBLIC_API_URL` — the example
already points it at `http://localhost:8000`, correct for local dev.

## 3. (Optional) Install Ollama — skip if using Gemini

```bash
brew install ollama        # macOS; see ollama.com for other platforms
ollama pull llama3.1
```

Ollama needs to be running on your **host machine** (not in Docker) —
the backend container reaches it automatically via
`host.docker.internal`, already configured in `docker-compose.yml`.

## 4. Start the backend (Postgres + ChromaDB + API + worker)

```bash
docker compose up -d --build
```

This builds the image, runs database migrations automatically
(`entrypoint.sh`), and starts four containers:

| Service | Address | What it is |
|---|---|---|
| `app` | http://localhost:8000 | FastAPI backend — Swagger docs at `/docs` |
| `worker` | *(no exposed port)* | Background document processing |
| `db` | localhost:5432 | PostgreSQL |
| `chroma` | localhost:8001 | Vector database server |

Check everything came up healthy:

```bash
docker compose ps
```

## 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** — register an account, upload a
document, and start chatting.

## 6. Or skip the UI and try the API directly

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"YourPass123!"}'

# Log in (copy access_token from the response)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"YourPass123!"}'

# Upload a document
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@your-document.pdf"

# Ask a question about it
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"question":"What does this document say?"}'
```

## Running the test suite

```bash
pytest -v \
  --ignore=tests/test_gemini.py \
  --ignore=tests/test_settings.py \
  --ignore=tests/test_bm25.py \
  --ignore=tests/test_chunker.py \
  --ignore=tests/test_embedding.py \
  --ignore=tests/test_retrieval.py \
  --ignore=tests/test_vector_stats.py \
  --ignore=tests/test_connections.py \
  --ignore=tests/test_llm.py
```

This is exactly what CI runs (`.github/workflows/ci.yml`) — the
excluded files are documented pre-existing failures, explained inline
in that workflow.

## Stopping / resetting

```bash
docker compose down       # stop containers, keep all data
docker compose down -v    # stop containers AND wipe all data - fresh start
```

## Running the backend without Docker (native/manual dev)

Only needed if you specifically don't want Docker for the backend —
Docker Compose (step 4) is the supported, tested path.

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# You still need a running Postgres and a running Chroma server -
# either point .env at existing ones, or start just those two services:
#   docker compose up -d db chroma

alembic upgrade head
uvicorn app.main:app --reload
```

## Quick command reference

| Task | Command |
|---|---|
| Start everything (backend) | `docker compose up -d --build` |
| Stop everything, keep data | `docker compose down` |
| Stop everything, wipe data | `docker compose down -v` |
| View backend logs | `docker compose logs app -f` |
| View worker logs | `docker compose logs worker -f` |
| Run backend tests | `pytest -v --ignore=...` (full command above) |
| Start frontend dev server | `cd frontend && npm run dev` |
| Build frontend for production | `cd frontend && npm run build` |
| Lint frontend | `cd frontend && npm run lint` |
| Run DB migrations manually | `alembic upgrade head` |
| Generate a JWT secret | `python -c "import secrets; print(secrets.token_hex(32))"` |
| Full pipeline smoke test | `bash scripts/check_pipeline.sh` |

---

# 🚀 Project Vision

Large Language Models (LLMs) do not have access to private organizational data.

RAG solves this limitation by combining:

- Document processing
- Text extraction
- Intelligent chunking
- Embedding generation
- Vector similarity search
- Large Language Models


Example:

### User Question

```
What is the company leave policy?
```

### RAG Pipeline

```
User Question

        ↓

Convert question into embedding

        ↓

Search relevant document chunks

        ↓

Retrieve matching context

        ↓

Send context + question to LLM

        ↓

Generate accurate answer
```

---

# 🏗️ System Architecture

```
                         Client

                           |
                           |

                        FastAPI

                           |

              Document Processing Layer

                           |

        +------------------+------------------+

        |                  |                  |

   File Storage        Parser Service     Chunking Service


                           |

                  Embedding Generation


                           |

                  Vector Database


                           |

                   Semantic Retrieval


                           |

                         LLM


                           |

                       Final Answer
```

---

# ✨ Implementation Roadmap

The project is developed incrementally following production engineering practices.

---

# ✅ Sprint 1 - Project Setup

## Objective

Create a scalable backend foundation.

## Implemented

- FastAPI project initialization
- Application entry point
- Modular folder structure
- Dependency management
- Virtual environment setup


## Architecture

```
app

├── main.py

├── api

├── services

├── models

├── schemas

└── core
```

---

# ✅ Sprint 2 - Document Upload

## Objective

Allow users to upload documents.

## Implemented

- File upload API
- File validation
- File type checking
- Unique file naming
- Storage service


Supported formats:

```
.pdf
.docx
.txt
```


## API Flow

```
Upload File

    ↓

Validate Extension

    ↓

Generate UUID

    ↓

Save File

    ↓

Return Metadata
```

---

# ✅ Sprint 3 - Document Parsing

## Objective

Extract readable text from documents.


Implemented:

- PDF extraction
- DOCX extraction
- TXT extraction
- Parser abstraction
- Error handling


## Libraries Used


### PyMuPDF

Purpose:

Extract text from PDF files.


Why?

- Fast
- Production stable
- Handles complex PDFs


---

### python-docx

Purpose:

Read Microsoft Word documents.


---

## Parser Design

Before:

```
API

 |
 |
PDF Logic
DOCX Logic
TXT Logic
```


After:

```
API

 |

ParserService

 |

PDFParser
DOCXParser
TXTParser
```

Benefits:

- Easy testing
- Easy extension
- Separation of responsibilities

---

# ✅ Sprint 4 - Intelligent Chunking


## Objective

Convert large documents into smaller meaningful pieces.


Example:


Before:

```
10 page document
```

After:

```
Chunk 1

Chunk 2

Chunk 3

Chunk 4
```


Implemented:

- Recursive text splitting
- Configurable chunk size
- Chunk overlap
- Metadata support


## Library Used


### LangChain Text Splitters


Purpose:

Intelligent document splitting.


Why?

Because simple string splitting breaks context.


Example:


Bad:

```
"The company policy"

"allows employees"
```


Good:

```
"The company policy allows employees"
```


---

# ✅ Sprint 4.1 - Chunk Storage


Implemented:

- Document ID tracking
- Chunk models
- Chunk persistence
- Metadata storage


Each chunk contains:


```json
{
"text":"employee leave policy",
"document_id":"uuid",
"metadata":{
"type":"pdf"
}
}
```

---

# ✅ Sprint 5 - Embedding Generation


## Objective

Convert text into numerical vectors.


Example:


Input:

```
Artificial Intelligence
```


Output:


```
[
0.123,
-0.453,
0.782
]
```


These vectors represent semantic meaning.


---

## Library Used


### Sentence Transformers


Purpose:

Generate text embeddings.


Why?

Traditional keyword search:

```
car
```

does not understand:


```
automobile
vehicle
transport
```


Embedding search understands semantic relationships.


---

# ✅ Sprint 5.1 - AI Model Registry


## Problem


Loading AI models repeatedly is expensive.


Bad:

```
Request 1

Load Model


Request 2

Load Model


Request 3

Load Model
```


Solution:


```
Application Startup

        ↓

Load Model Once

        ↓

Reuse Everywhere
```


Implemented:

- Singleton model loading
- Central AI registry
- Shared model instance


---

# ✅ Sprint 5.2 - Configuration Management


Implemented:

- Environment based configuration
- Pydantic settings
- External model configuration


Example:


`.env`

```env
EMBEDDING_MODEL=all-MiniLM-L6-v2

CHUNK_SIZE=1000

CHUNK_OVERLAP=200
```


Benefits:

- No hardcoded values
- Environment flexibility
- Production ready

---

# 🛠️ Tech Stack


## Backend

| Technology | Purpose |
|---|---|
| Python | Programming Language |
| FastAPI | Backend Framework |
| Uvicorn | ASGI Server |
| Pydantic | Data Validation |


---

## AI / ML

| Technology | Purpose |
|---|---|
| Sentence Transformers | Embeddings |
| HuggingFace Models | NLP Models |
| LangChain | Text Processing |


---

## Document Processing


| Library | Purpose |
|---|---|
| PyMuPDF | PDF Extraction |
| python-docx | DOCX Extraction |


---

## Testing


| Tool | Purpose |
|---|---|
| PyTest | Unit Testing |

---

# 📂 Project Structure


```
rag-chatbot

│

├── app

│   ├── main.py

│   │

│   ├── api

│   │

│   ├── core

│   │   ├── config.py

│   │   └── ai_registry.py

│   │

│   ├── services

│   │   ├── storage.py

│   │   ├── parser.py

│   │   ├── chunker.py

│   │   └── embedding.py

│   │

│   ├── models

│   │

│   └── schemas


├── tests


├── docs


├── requirements.txt


├── .env.example


├── README.md


└── .gitignore
```

---

# ⚙️ Local Setup, Running, and Testing

This was written during Sprint 1, before Postgres, ChromaDB, Docker
Compose, the worker, auth, or the frontend existed — it's kept here as
history, not instructions. **See [⚡ Getting Started](#getting-started)
at the top of this file for the current, accurate setup guide, exact
commands, and full environment variable list.**

---

# 🧠 Engineering Principles


## SOLID Principles


### Single Responsibility Principle


Each service handles one responsibility.


Example:


```
StorageService

ParserService

ChunkingService

EmbeddingService
```


---

## Separation of Concerns


API Layer:

```
Request handling
```


Service Layer:

```
Business logic
```


Models:

```
Data representation
```


---

# Design Patterns Used


## Singleton Pattern


Used for AI model loading.


Purpose:

- Reduce memory usage
- Improve performance


---

## Registry Pattern


Central management of AI resources.


---

## Configuration Pattern


Environment driven configuration.


---

# ✅ Sprint 6 - Vector Database Integration

## Objective

Persist embeddings so retrieval survives restarts and scales beyond memory.

## Implemented

- ChromaDB persistent client
- Collection-based vector storage
- Similarity search by embedding
- Chunk-to-vector linkage


---

# ✅ Sprint 7 - Semantic Retrieval

## Objective

Turn a user question into ranked, relevant document chunks.

## Implemented

- Query embedding generation
- Top-K similarity search
- Distance-threshold filtering
- Retrieval service abstraction layer (Sprint 7.1)
- Centralized application configuration (Sprint 7.2)


---

# ✅ Sprint 8 - LLM Integration

## Objective

Generate natural-language answers from retrieved context.

## Implemented

- Configurable LLM registry
- Ollama provider
- Gemini provider
- Provider abstraction (`app/services/llm/base.py`)


---

# ✅ Sprint 9 - Complete RAG Pipeline

## Objective

Wire retrieval and generation into a single conversational system.

```
Question

 ↓

Query Enhancement / Expansion

 ↓

Hybrid Retrieval (Vector + BM25)

 ↓

Cross-Encoder Reranking

 ↓

Context Window Management

 ↓

LLM

 ↓

Hallucination Guard

 ↓

Answer + Source Citations
```

## Implemented

- End-to-end `/chat` API
- Prompt builder with context-aware generation
- Conversation memory (multi-turn history, `conversation_id`)
- Hybrid search (BM25 + vector fusion)
- Cross-encoder reranking
- Conversation-aware query rewriting
- Query expansion
- Context window manager (dedup, compression, ranking, formatting)
- Source references / context-aware citations
- Hallucination guard
- RAG and search evaluation metrics


---

# ✅ Sprint 10 - Enterprise Features

## Objective

Make the system multi-user and production-safe.

## Implemented

- PostgreSQL integration via SQLAlchemy (async)
- Alembic migrations (`users`, `documents` tables)
- JWT-based authentication (register / login / `/auth/me`)
- Password hashing and security utilities
- Document ownership model
- Per-user document listing, retrieval, and deletion
- Access-scoped retrieval — RAG chat only searches documents owned by the authenticated user


---

# ✅ Sprint 11 - Production Engineering

## Objective

Make the application runnable anywhere with a single command, and
gate every change with an automated test run.

## Implemented

- Multi-stage `Dockerfile` (build stage installs deps into a venv,
  runtime stage is `python:3.11-slim` + `libgomp1` for PyTorch,
  runs as a non-root user, ships a `/health`-based `HEALTHCHECK`)
- `entrypoint.sh` - runs `alembic upgrade head` before starting
  `uvicorn`, so a fresh container always has an up-to-date schema
- `docker-compose.yml` - app + PostgreSQL, named volumes for every
  writable directory (`uploads/`, `chunks/`, `embeddings/`,
  `vector_db/`, `storage/bm25/`, `logs/`) so data survives restarts
- `.dockerignore` - keeps `venv/`, `.git/`, `.env`, and generated
  data out of the build context and image
- GitHub Actions CI (`.github/workflows/ci.yml`) - spins up a real
  Postgres service, runs migrations, then runs the test suite on
  every push/PR to `master`
- `pytest-asyncio` + `asyncio_mode = "auto"` - fixes previously
  non-running bare `async def` tests

## Running Locally with Docker

See [⚡ Getting Started](#getting-started) at the top of this file —
same commands, kept in one place so they don't drift out of sync with
each other.

## Known Limitations

- Single `uvicorn` worker per container (the embedding model is a
  process-local singleton; scaling workers/replicas is a Sprint 12
  deployment concern)
- CI excludes 8 pre-existing failing tests unrelated to this sprint
  (stale fixtures, a hardcoded provider assumption, one unregistered
  route, one event-loop conflict) - documented inline in the workflow


---

# ✅ Sprint 12 - Deployment

## Objective

Get the app running on a real, publicly-reachable host, with database
and secrets managed outside the codebase.

## Platform

**Render**, chosen over AWS/Azure for this stage: a single
`render.yaml` blueprint versus manually wiring ECS/Fargate + RDS +
IAM (AWS) or Container Apps + Azure Database for PostgreSQL (Azure).
AWS/Azure are worth revisiting later specifically for that
experience - not needed to get this project live.

## Implemented

- `render.yaml` - Blueprint defining a Docker-based web service
  (built from the Sprint 11 `Dockerfile`, no changes to it needed)
  plus a managed free-tier PostgreSQL database
- `entrypoint.sh` - now binds to Render's dynamically-assigned
  `$PORT` (falls back to `8000` locally, so Docker Compose is
  unaffected), and derives driver-qualified `DATABASE_URL` /
  `DATABASE_URL_SYNC` from Render's plain Postgres connection string
  at container startup, without touching `app/core/config.py`
- Secrets (`JWT_SECRET_KEY`, `GEMINI_API_KEY`) declared as
  `sync: false` in the blueprint - Render prompts for them in its
  dashboard rather than storing them in git

## Free Tier Tradeoff

Render's free web services cannot attach a persistent disk, and free
Postgres is capped at 1GB and deleted 30 days after creation. This
app writes documents/vectors/BM25 index to the local filesystem
(`vector_db/`, `storage/bm25/`, `uploads/`, `chunks/`, `embeddings/`)
- on the free tier, that data does **not** survive a redeploy or a
scale-to-zero cold start. Fine for a live demo; upgrade the web
service to a paid plan with an attached disk, and the database past
its 30-day window, once persistence actually matters.

## LLM Provider

Only `gemini` works as `LLM_PROVIDER` on Render - `ollama` needs a
locally reachable daemon, which doesn't exist on a cloud host. A
real `GEMINI_API_KEY` must be set in Render's dashboard for `/chat`
to work; every other route works without one.


---

# 🎯 Learning Outcomes


This project demonstrates:


✅ AI Engineering

✅ LLM Application Development

✅ RAG Architecture

✅ NLP Pipelines

✅ Vector Search

✅ Backend Engineering

✅ Production AI System Design


---

# 👨‍💻 Author


Built as an AI Engineering portfolio project.

---

⭐ If this project helped you, consider starring the repository.
