# Libraries

Every dependency actually imported and used by `app/`, verified against
`requirements.txt` and real `import` statements — not just what's listed
in the file. A separate section at the end lists what's installed but
**not** used.

## API

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **FastAPI** | 0.139.0 | The web framework — all routing, request/response models, dependency injection | Async-native, automatic request validation via Pydantic, built-in OpenAPI docs | Flask (simpler, sync by default), Django (batteries-included, heavier) |
| **Uvicorn** | 0.51.0 | ASGI server that actually runs the FastAPI app | Required to serve any ASGI app; fast, widely used | Hypercorn, Daphne |

## Validation / Config

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **Pydantic** | 2.13.4 | Every request/response schema (`app/schemas/`), internal data models (`app/models/`) | Type-validated data classes with automatic FastAPI integration | Marshmallow, attrs + manual validation |
| **pydantic-settings** | 2.14.2 | `app/core/config.py`'s `Settings` class — loads and type-checks every `.env` value | Fails fast at startup if a config value has the wrong type, instead of failing deep in unrelated code later | `python-decouple`, manual `os.environ` reads |
| **python-dotenv** | 1.2.2 | Loads `.env` into the process (used internally by pydantic-settings) | Standard way to keep secrets out of source control | — |

## Database

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **SQLAlchemy** | 2.0.51 | Async ORM — `app/database/models/`, `app/database/repositories/` | Python objects instead of hand-written SQL, async engine matches FastAPI's async request handlers | Raw SQL + a driver, Tortoise ORM, Django ORM |
| **asyncpg** | 0.31.0 | The actual async Postgres driver SQLAlchemy uses at runtime | Fast, async-native Postgres driver | `psycopg` (v3, has async support too) |
| **psycopg2-binary** | 2.9.12 | The *sync* Postgres driver — used only by Alembic, which doesn't run async | Alembic's migration runner needs a sync driver | — |
| **Alembic** | 1.18.5 | Database schema migrations (`migrations/`) | Version-controlled, repeatable schema changes | Manual SQL migration scripts, Django migrations (if using Django) |

## Document Processing

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **PyMuPDF** (`fitz`) | 1.28.0 | `ParserService.parse_pdf()` — PDF text extraction | Fast, handles most real-world PDFs correctly, no OCR overhead for non-scanned files | `pypdf` (installed here but unused), `pdfplumber`, Unstructured, cloud OCR services |
| **python-docx** | 1.2.0 | `ParserService.parse_docx()` — DOCX text extraction | Reads `.docx` paragraph structure directly | Apache Tika, `mammoth` |

## Chunking

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **langchain-text-splitters** | 1.1.2 | `RecursiveCharacterTextSplitter` in `ChunkingService` | Splits on paragraph/sentence/word boundaries in that preference order, instead of naive fixed-length cuts | Semantic chunking (split by embedding-similarity shifts), structure-aware chunking (split by document headings/sections) |

## Embeddings & Reranking

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **sentence-transformers** | 5.6.0 | `EmbeddingService` (`SentenceTransformer`, model `all-MiniLM-L6-v2`) and `Reranker` (`CrossEncoder`, model `cross-encoder/ms-marco-MiniLM-L-6-v2`) | One library provides both the bi-encoder (fast, independent scoring) used for embeddings and the cross-encoder (slower, joint scoring) used for reranking | OpenAI/Cohere/Voyage embedding APIs, BGE/E5 open models |
| **torch** | 2.13.0 | The tensor runtime underneath `sentence-transformers` | Required dependency of `sentence-transformers`, not called directly by this app's own code | — |
| **transformers** | 5.13.1 | Hugging Face model loading, used internally by `sentence-transformers` | Required dependency, not called directly | — |

## Vector Database

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **chromadb** | 1.5.9 | `VectorStoreService`, connected via `ChromaClient`'s `HttpClient` to a separate Chroma server | Purpose-built approximate-nearest-neighbor search, simple to run as a Docker service | Pinecone, Qdrant, Weaviate, Milvus, `pgvector`, Elasticsearch/OpenSearch, Redis |

## Keyword Search

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **rank-bm25** | 0.2.2 | `BM25SearchService` (`BM25Okapi`) — the keyword half of hybrid search | Lightweight, in-process BM25 implementation, no separate service to run | Elasticsearch, OpenSearch (both also give you a distributed, persistent keyword index instead of a pickled in-process one) |

## LLM

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **google-generativeai** | 0.8.6 | `GeminiService` | Official Gemini SDK | `openai` SDK (for OpenAI/Azure OpenAI), `anthropic` SDK, `boto3` (Bedrock) |
| **ollama** | 0.6.2 | `OllamaService` | Official Python client for a locally-running Ollama daemon | Direct HTTP calls to any self-hosted inference server (vLLM, TGI, etc.) |

## Authentication

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **python-jose** | 3.5.0 | `create_access_token()` / `get_current_user()` — JWT encode/decode | Standard JWT library for Python, works cleanly with FastAPI's dependency system | `PyJWT` |
| **passlib** | 1.7.4 | `hash_password()` / `verify_password()`, via `CryptContext(schemes=["bcrypt"])` | Wraps bcrypt with a stable API | `bcrypt` directly, `argon2-cffi` |
| **bcrypt** | 4.1.3 | The actual hashing algorithm passlib calls | Deliberately slow hashing — expensive to brute-force | Argon2 (newer, increasingly preferred for new systems) |

## File Upload

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **python-multipart** | 0.0.32 | Required by FastAPI/Starlette to parse `multipart/form-data` uploads (`UploadFile`) | FastAPI's `File(...)`/`UploadFile` support depends on it being installed | — |

## Testing

| Library | Version | Used For | Why | Alternative |
|---|---|---|---|---|
| **pytest** | 9.1.1 | The test runner for all of `tests/` | Standard Python testing framework | `unittest` (stdlib) |
| **pytest-asyncio** | 1.4.0 | Lets `async def test_...()` functions actually execute (`asyncio_mode = "auto"`) | Without it, pytest silently skips async test functions instead of failing | — |

## Installed but not used by this application's code

Verified by grepping `app/` for imports of each — these appear in
`requirements.txt` (as direct or transitive dependencies) but nothing in
the actual application imports them:

| Library | Why it's listed here |
|---|---|
| `langchain`, `langchain-classic`, `langchain-community`, `langchain-core`, `langchain-openai` | Only `langchain_text_splitters` (a separate package) is actually used, for `RecursiveCharacterTextSplitter` |
| `langgraph`, `langgraph-checkpoint`, `langgraph-prebuilt`, `langgraph-sdk` | Not imported anywhere |
| `langsmith` | Not imported anywhere |
| `openai` | Not imported anywhere — Gemini and Ollama are the only wired-up LLM providers |
| `pypdf` | Not imported — PDF parsing uses PyMuPDF (`fitz`) exclusively |
| `tiktoken` | Referenced only in a code comment in `context_window_manager.py` ("Later we can replace with tiktoken") — never imported |
| `black`, `ruff`, `isort` | Dev-time formatting/linting tools, not runtime dependencies |

Do not assume any of the above is part of the active pipeline just
because it's installed.
