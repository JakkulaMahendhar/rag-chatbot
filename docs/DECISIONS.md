# Decisions

Architecture Decision Record style notes for the major technology
choices in this project. Where the reasoning is directly evidenced by
the code or by this project's own documented build history
(`docs/sprints/`), it's stated as fact. Where it isn't, it's explicitly
labeled as inferred.

---

### Why FastAPI?

**Decision:** FastAPI as the web framework.
**Why:** Async-native — every I/O-bound step in this pipeline (database
queries, ChromaDB HTTP calls, LLM API calls) is `await`ed rather than
blocking a worker thread. Automatic request/response validation via
Pydantic integrates directly with the schemas already needed for the
API.
**Benefits:** Type-checked request bodies for free, auto-generated
OpenAPI docs (`/docs`), first-class async support.
**Trade-offs:** Smaller ecosystem than Django (no built-in admin panel,
ORM, or auth system — all wired up manually here).
**Alternative:** Flask (simpler, but synchronous by default — every
waiting network call would block the whole worker), Django (heavier,
more built-in).

---

### Why ChromaDB, and why as its own server?

**Decision:** ChromaDB for vector storage, running as a separate server
process rather than embedded in the FastAPI app.
**Why (documented, not inferred):** the project originally ran ChromaDB
embedded (`PersistentClient`, direct file access). Once a separate
background worker process was introduced for document processing, both
the web app and the worker independently opened embedded storage handles
against the same files — ChromaDB's embedded client isn't designed for
concurrent multi-process access, and this produced a real, reproduced
bug (`chromadb.errors.InternalError: Error finding id`). Running it as
its own server, both processes connecting over HTTP, fixed it. Full
story in
[`docs/sprints/06-vector-database-chromadb.md`](sprints/06-vector-database-chromadb.md).
**Benefits:** Purpose-built ANN search, simple to run as one more Docker
Compose service, no external paid dependency.
**Trade-offs:** Self-hosted — no managed backups/scaling, and this
project runs a single ChromaDB instance with no replication.
**Alternative:** Pinecone, Qdrant, Weaviate, `pgvector`.

---

### Why Sentence Transformers?

**Decision:** the `sentence-transformers` library for both embeddings and
reranking.
**Why:** *Likely rationale based on implementation* — a single library
provides both the bi-encoder (`SentenceTransformer`, for fast independent
embedding) and the cross-encoder (`CrossEncoder`, for precise joint
reranking) used in this pipeline, and both run entirely locally with no
API key or per-call cost.
**Benefits:** No external API dependency for the core retrieval loop; one
library covers two distinct roles.
**Trade-offs:** Both models run on the same machine as the app (or
worker) — memory and CPU cost is paid locally rather than offloaded to a
hosted API.
**Alternative:** OpenAI/Cohere embedding + rerank APIs (hosted, no local
compute, but a per-call cost and network dependency).

---

### Why `all-MiniLM-L6-v2` specifically?

**Decision:** `all-MiniLM-L6-v2` as the embedding model
(`settings.embedding_model`).
**Why:** *Likely rationale based on implementation* — it's one of the
smallest widely-used sentence-transformer models (~90MB, 384 dimensions),
which matters directly because this project is also documented
(`docs/sprints/12-deployment-and-worker-queue.md`) to have hit a 512MB
memory ceiling on its original deployment target. A smaller embedding
model is a real, concrete lever against that constraint.
**Benefits:** Fast on CPU, no GPU required, small memory footprint.
**Trade-offs:** Lower retrieval fidelity than larger embedding models
(768/1024+ dimensions) for nuanced or domain-specific text.
**Alternative:** OpenAI `text-embedding-3-*`, Cohere, Voyage, BGE, E5 —
generally higher accuracy, generally larger or API-hosted.

---

### Why the current chunk size (1000) and overlap (200)?

**Decision:** `chunk_size=1000`, `chunk_overlap=200`
(`app/core/config.py`), applied globally to every document.
**Why:** *Likely rationale based on implementation* — these are common
default starting values for `RecursiveCharacterTextSplitter` in the
LangChain ecosystem, not values derived from measuring this project's own
retrieval quality against a test set (no such evaluation exists in this
codebase — see [`docs/PRODUCTION_EVOLUTION.md`](PRODUCTION_EVOLUTION.md)).
**Benefits:** Simple, one global setting, no per-document tuning
complexity.
**Trade-offs:** No adaptation for different document types — a dense
legal document and a narrative document get chunked identically.
**Alternative:** Semantic or structure-aware chunking, or per-document-type
tuning.

---

### Why overlap at all?

**Decision:** chunks overlap by 200 characters.
**Why:** directly evidenced by the splitter's own design intent —
without overlap, a chunk boundary falling mid-idea (e.g. right after "30
days of annual leave") would leave the next chunk starting without its
subject. Overlap means a search matching near a boundary still retrieves
a chunk with full surrounding context.
**Trade-offs:** Slightly more stored text and mild content duplication
across adjacent chunks (no dedup-of-overlap logic exists — the only
deduplication implemented, `ContextDeduplicator`, only catches *exact*
full-content duplicates, not partial overlap).

---

### Why a `RetrievalService` abstraction?

**Decision:** retrieval logic lives behind `RetrievalService`, which
itself wraps `HybridSearchService`, rather than API routes calling
`VectorStoreService`/`BM25SearchService` directly.
**Why:** *Likely rationale based on implementation* — both `POST /chat`
(via `RAGChatService`) and `POST /search` (via `SearchService`) need the
same user-scoped hybrid retrieval; `RetrievalService` is the one place
that resolves document ownership and runs the search, so both callers get
identical behavior without duplicating logic.
**Benefits:** One place to change retrieval behavior; ownership scoping
enforced structurally rather than re-implemented per caller.
**Trade-offs:** An extra layer to trace through when debugging — a
request passes through `RAGChatService` → `RetrievalService` →
`HybridSearchService` → `VectorStoreService`/`BM25SearchService` before
reaching the actual search calls.

---

### Why service-layer abstractions in general (the `app/services/` split)?

**Decision:** business logic lives in `app/services/`, API routes in
`app/api/` stay thin, database access goes through `app/database/repositories/`.
**Why:** *Likely rationale based on implementation* — this is a
conventional layered-architecture split (API layer / service layer /
data layer). It shows a real, verifiable payoff in this codebase: adding
authentication (a later addition) required no changes to
`ParserService`, `ChunkingService`, or `EmbeddingService` — auth was
wired in entirely at the API layer via FastAPI's `Depends()`.
**Benefits:** Business logic is callable from multiple entry points (the
worker process calls `DocumentProcessingService` directly, with no HTTP
layer involved at all).
**Trade-offs:** More files and indirection for a project this size; some
inconsistency exists between `app/models/` (meant for internal shapes)
and `app/schemas/` (meant for API contracts) — not perfectly enforced
throughout.

---

### Why Gemini (and why also support Ollama)?

**Decision:** two LLM providers behind one interface, Gemini as a cloud
option and Ollama as a free local option.
**Why:** *Likely rationale based on implementation.* Ollama requires a
locally (or network-)reachable daemon — viable for local development at
zero API cost, but not viable on a typical cloud host with no such daemon
reachable. Gemini provides a cloud fallback for exactly that case. Both
being available behind `LLMService` means switching is a config value
(or, since a later addition, a per-request field), not a code change.
**Benefits:** No forced dependency on a paid API for local development;
a working cloud option when a local daemon isn't available.
**Trade-offs:** Neither `generate()` call configures temperature, output
length, or retries — both rely entirely on SDK defaults (see
[`docs/LLM_INTEGRATION.md`](LLM_INTEGRATION.md)).
**Alternative:** OpenAI, Anthropic, Azure OpenAI, Bedrock, self-hosted
models.

---

### Why not fine-tuning?

**Decision:** no model fine-tuning anywhere in this pipeline —
retrieval-augmented prompting only.
**Why:** RAG and fine-tuning solve different problems. Fine-tuning
changes a model's weights to change its *behavior/style*, and doesn't
reliably teach it new, precise, easily-updated facts — adding a new
uploaded document would mean retraining. RAG instead retrieves fresh,
exact document content at request time and puts it directly in the
prompt, so newly uploaded documents are usable immediately with no
retraining step. This is a property of the RAG approach in general, not
a project-specific choice this codebase argues for explicitly — but it
is the reason this architecture (retrieve + prompt) was built instead of
a fine-tuning pipeline.
**Trade-offs:** Every request pays the cost of retrieval plus a larger
prompt (more input tokens) instead of a fine-tuned model that might need
less context per call.
