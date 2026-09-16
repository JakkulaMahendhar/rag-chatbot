# RAG Pipeline

This is the detailed, step-by-step explanation of how this application
turns an uploaded document and a question into a grounded answer. Every
claim here is backed by a specific file and class.

**Running example**, used consistently through this document:

> A user uploads `leave_policy.pdf`, which contains the sentence:
> *"Employees receive 30 days of annual leave after completing one year
> of service."*
> They then ask: *"How many annual leave days do employees receive?"*

---

## 1. Document Upload

**Endpoint:** `POST /upload` — `app/api/upload.py`

```python
@router.post("/upload", status_code=202, response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentRegistrationService = Depends(get_document_registration_service),
):
```

**Request:** `multipart/form-data` with the file, and an `Authorization:
Bearer <JWT>` header (the route requires a logged-in user).

**Validation:** the extension must be `.pdf`, `.docx`, or `.txt`
(`ALLOWED_TYPES` in `upload.py`); anything else is rejected with `400`
before any file handling happens.

**File handling:** `StorageService.save_file()` (`app/services/storage.py`)
renames the file to a random UUID (e.g. `leave_policy.pdf` →
`a1b2c3d4-....pdf`) and writes it to `uploads/`. The original filename is
never used as the on-disk name — it's kept separately in Postgres.

**What happens next:** `DocumentRegistrationService.register()` creates a
`Document` row (`app/database/models/document.py`) with `status="pending"`
and returns immediately. The response is `202 Accepted`:

```json
{
  "document_id": "14",
  "filename": "leave_policy.pdf",
  "status": "pending",
  "message": "Document uploaded and queued for processing."
}
```

The actual parsing/chunking/embedding has **not** happened yet — it's
picked up by a separate worker process. The client polls `GET
/documents/{id}` to see `status` move from `pending` → `processing` →
`completed` (or `failed`, with `error_message` set).

---

## 2. Document Parsing

**File:** `app/services/parser.py`, class `ParserService`

```python
@staticmethod
def parse(file_path: Path) -> str:
    extension = file_path.suffix.lower()
    if extension == ".pdf":
        return ParserService.parse_pdf(file_path)
    if extension == ".docx":
        return ParserService.parse_docx(file_path)
    if extension == ".txt":
        return ParserService.parse_txt(file_path)
    raise ValueError("Unsupported document type")
```

| Format | Library | Method |
|---|---|---|
| PDF | **PyMuPDF**, imported as `fitz` | `fitz.open(path)`, then `page.get_text()` for every page, concatenated |
| DOCX | **python-docx** | `Document(path).paragraphs`, joined with `\n` |
| TXT | Python's built-in `open()` | `file.read()`, UTF-8 |

**Input:** a file path (e.g. `uploads/a1b2c3d4-....pdf`).
**Output:** one plain-text string.
**Why PyMuPDF:** fast, actively maintained, handles the majority of
real-world (non-scanned) PDFs correctly.
**Alternative:** `pypdf` is listed in `requirements.txt` but is **not**
imported anywhere in the app — PyMuPDF is the only PDF library actually
in use.

---

## 3. Text Extraction

Using the running example, `leave_policy.pdf` (assume it's one page)
produces:

```
Document:
"Employees receive 30 days of annual leave after completing one year of service."

Extracted text (ParserService.parse output):
"Employees receive 30 days of annual leave after completing one year of service."
```

For a real multi-page PDF, `parse_pdf()`'s loop (`text += page.get_text()`)
concatenates every page into **one single string with no marker between
pages**. This is a real, direct consequence of the implementation: this
system cannot tell you which page an answer came from, because that
information is discarded at this step. No other formatting (headings,
tables, fonts) is preserved either — `page.get_text()` and
`python-docx`'s `.paragraphs` both return plain text only.

---

## 4. Chunking

**File:** `app/services/chunker.py`, class `ChunkingService`

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

self.splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,       # 1000
    chunk_overlap=settings.chunk_overlap, # 200
    length_function=len,
)
```

**Why chunking is required:** an embedding model produces one vector per
input; a whole document embedded as a single vector would blur every
topic in it together, and an LLM has a finite context window. Splitting
into smaller, focused pieces lets retrieval find the *specific* passage
relevant to a question instead of returning (or having to read) the
entire document every time.

```
leave_policy.pdf (full text)
        ↓
   RecursiveCharacterTextSplitter
        ↓
Chunk "14-0": "Employees receive 30 days of annual leave after
               completing one year of service."
```

For a short document like this one, the whole thing fits in a single
chunk. For a longer one, `RecursiveCharacterTextSplitter` tries
paragraph breaks first, then sentence breaks, then word breaks — only
cutting mid-word as a last resort — so it prefers not to split a sentence
like "Employees receive 30 days..." across two chunks.

**Configured values** (`app/core/config.py`):
- `chunk_size = 1000` characters
- `chunk_overlap = 200` characters

**Why overlap exists:** if a chunk boundary happens to fall right after
"Employees receive 30 days of annual leave," the next chunk would start
mid-thought without it. Overlap means the last 200 characters of one
chunk are repeated at the start of the next, so a search that matches
near a boundary still gets full context.

**Metadata attached to each chunk:**

```json
{
  "document_id": "14",
  "user_id": "7",
  "filename": "a1b2c3d4-....pdf",
  "type": ".pdf",
  "chunk_id": "14-0"
}
```

This travels with the chunk all the way into ChromaDB and is what later
powers per-user filtering and source citations.

**Trade-off:**

| Chunk size | Pros | Cons |
|---|---|---|
| Small | Precise retrieval — a match is tightly relevant | Less surrounding context per chunk, more chunks to manage |
| Large | More context per chunk | Noisier matches (a chunk can contain the answer plus unrelated text), higher token cost per chunk sent to the LLM |

This project uses one fixed global value (1000/200) for every document —
there's no per-document-type tuning.

---

## 5. Embeddings

**File:** `app/services/embedding.py`, class `EmbeddingService`

```python
def generate(self, chunks: list[DocumentChunk]) -> list[DocumentEmbedding]:
    for chunk in chunks:
        vector = self.model.encode(chunk.content, convert_to_numpy=True)
        ...

def generate_query_embedding(self, text: str) -> list[float]:
    vector = self.model.encode(text, convert_to_numpy=True)
    return vector.tolist()
```

```
Text: "Employees receive 30 days of annual leave..."
        ↓
   all-MiniLM-L6-v2 (SentenceTransformer)
        ↓
Vector: [-0.0869, -0.0369, -0.0424, ... ]   (384 numbers)
```

An embedding is a list of numbers that represents the *meaning* of a
piece of text — two pieces of text with similar meaning produce vectors
that are numerically close together, even if they use different words.

**Model:** `all-MiniLM-L6-v2` (`settings.embedding_model`,
`app/core/config.py`), loaded via `sentence-transformers`. Produces
**384-dimensional** vectors.

**Same model, both directions:** `generate()` embeds document chunks at
ingestion time; `generate_query_embedding()` embeds the user's question
at query time — both call `self.model.encode(...)` on the exact same
loaded model instance. This is required: comparing vectors from two
different embedding models is meaningless, since each model has its own
internal geometry.

**Loaded once per process:** `EmbeddingService.__init__` calls
`AIServiceRegistry.get_embedding_model()` (`app/core/ai_registry.py`),
which loads `all-MiniLM-L6-v2` from disk exactly once and caches it —
every chunk and every question after that reuses the same in-memory
model instead of reloading it.

> **CURRENT:** `all-MiniLM-L6-v2`, ~90MB, runs on CPU, 384 dimensions.
> Chosen for being small and fast enough to run without a GPU or paid API
> — a real constraint for a project meant to run on modest infrastructure.
> It is not the most accurate embedding model available; larger models
> (768/1024+ dimensions) can capture more nuance at the cost of memory
> and speed.

> **INDUSTRY ALTERNATIVES:** OpenAI's `text-embedding-3-*` models, Cohere
> `embed-*`, Voyage AI, BGE (`BAAI/bge-*`), E5 (`intfloat/e5-*`), and
> multilingual variants of most of the above when the content isn't
> English-only. These are commonly chosen for higher retrieval accuracy
> or built-in multilingual support, generally at a higher cost (API fees
> or larger local models).

---

## 6. Vector Database

**File:** `app/services/vector_store.py`, class `VectorStoreService`

```
Document chunks
    ↓
Embeddings (all-MiniLM-L6-v2)
    ↓
ChromaDB collection "documents"
    ↓
Stored: id, document text, 384-dim vector, metadata
```

```python
self.collection.upsert(
    ids=[str(chunk.chunk_id) for chunk in chunks],       # "14-0"
    documents=[chunk.content for chunk in chunks],         # the chunk text
    embeddings=[e.embedding for e in embeddings],           # the 384-float vector
    metadatas=[chunk.metadata for chunk in chunks],         # document_id, user_id, filename, ...
)
```

**Collection:** one collection, named `"documents"`
(`self.client.get_or_create_collection(name="documents")`) — every user's
every document's chunks live in this same collection, distinguished only
by the `user_id`/`document_id` fields in each chunk's metadata.

**Persistence:** ChromaDB runs as its **own server** (the
`docker-compose.yml` `chroma` service, `chromadb/chroma:1.5.9`), not
embedded inside the FastAPI process. `ChromaClient`
(`app/services/chroma_client.py`) connects to it over HTTP:

```python
cls._client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
```

This matters because the web app and the worker are **separate
processes** both writing to the same vector store — ChromaDB's embedded,
file-based client is not designed for concurrent multi-process writes,
which was a real, reproduced bug in this project's history (see
[`docs/sprints/06-vector-database-chromadb.md`](sprints/06-vector-database-chromadb.md)).
Running it as a server both processes connect to over HTTP avoids that.

**Retrieval:** `collection.query(query_embeddings=[...], n_results=top_k,
where={...})` — ChromaDB returns the `n_results` stored vectors closest
to the query vector by **L2 (Euclidean) distance**, optionally filtered
by a `where` clause (used here to scope results to a specific set of
`document_id`s).

> **CURRENT:** ChromaDB, server mode.

> **INDUSTRY ALTERNATIVES:** Pinecone and Qdrant (managed/self-hosted
> vector databases built for larger scale and richer filtering), Weaviate
> (vector DB with built-in hybrid search), Milvus (large-scale, often
> Kubernetes-deployed), `pgvector` (adds vector search directly to an
> existing PostgreSQL database — attractive if you already run Postgres
> and don't want a second database to operate), Elasticsearch/OpenSearch
> and Redis (general-purpose search/data stores that also support vector
> search alongside their other capabilities).

---

## 7. Retrieval

**File:** `app/services/retrieval.py`, class `RetrievalService`

```
User Question: "How many annual leave days do employees receive?"
    ↓
Query Embedding (EmbeddingService.generate_query_embedding)
    ↓
HybridSearchService.search() — vector + BM25 (see section 8)
    ↓
Candidate chunks with hybrid_score
    ↓
Filtered by hybrid_score_threshold (0.30)
    ↓
Top settings.retrieval_top_k (5)
```

`RetrievalService` has three entry points, all in the same file:

- **`retrieve()`** — the low-level call: given a query embedding, query
  text, and a known list of `document_ids`, runs hybrid search and
  filters by score. Does not know about `user_id` — ownership must
  already be resolved before calling it.
- **`retrieve_for_user()`** — resolves `document_ids` for a `user_id` from
  Postgres, then calls `retrieve()`. Used by `POST /search`.
- **`multi_retrieve()`** — resolves `document_ids` once, then calls
  `retrieve()` **once per query variant** (see Query Expansion, section
  9 below) and merges + deduplicates the results by chunk ID. Used by
  `POST /chat`.

**Similarity/distance:** vector search returns ChromaDB's raw L2
distance; `HybridSearchService._normalize_distance()` converts it into a
0–1 similarity score with `1 / (1 + distance)` (not cosine similarity —
see [`docs/RETRIEVAL.md`](RETRIEVAL.md) for why this project doesn't use
cosine directly).

**Top-K in this codebase, at each stage:**

| Setting | Value | Used where |
|---|---|---|
| `top_k_vector` | 10 | How many candidates ChromaDB's vector search returns before fusion |
| `top_k_bm25` | 10 | How many candidates BM25 returns before fusion |
| `hybrid_top_k` | 10 | How many fused candidates `HybridSearchService` keeps |
| `retrieval_top_k` | 5 | Final count `RetrievalService.retrieve()` asks `HybridSearchService` for |
| `rerank_top_k` | 3 (hardcoded in `Reranker.rerank()` as `[:3]`, not read from settings) | Final count after cross-encoder reranking |

**Metadata returned with each chunk:** `document_id`, `chunk_id`,
`filename`, `content`, and a `score` (built by `SourceBuilder` into a
`SourceReference` — `app/models/source.py`).

---

## 8. Hybrid Search

> **CURRENT: hybrid search (vector + BM25) is implemented.** This is not
> a planned feature — it runs on every `/chat` and `/search` request.

**File:** `app/services/hybrid_search.py`, class `HybridSearchService`

```
Query
 ├── Vector Search (VectorStoreService, ChromaDB)
 │     → normalized: 1 / (1 + L2 distance)
 │
 └── BM25 (BM25SearchService, rank_bm25.BM25Okapi)
       → normalized: score / max(score in this result set)

            ↓
    Merge by chunk_id
    (a chunk found by only one method gets 0 for the other)
            ↓
    hybrid_score = vector_weight * vector_score + bm25_weight * bm25_score
    (0.6)                          (0.4)
            ↓
    Filter: hybrid_score >= hybrid_score_threshold (0.30)
            ↓
    Sort descending, take top_k
```

This is a **weighted-sum score fusion**, not Reciprocal Rank Fusion (see
below for what RRF is and how it differs).

```python
item["hybrid_score"] = (
    settings.vector_weight * item["vector_score"]
    + settings.bm25_weight * item["bm25_score"]
)
```

**Why combine them:** for the question *"How many annual leave days do
employees receive?"*, vector search matches on meaning — it would still
find the chunk even if the question said *"How much yearly vacation do
staff get?"* BM25 (`app/services/bm25_search.py`, using
`rank_bm25.BM25Okapi`) matches on the literal words in the question —
it's strong for exact terms, IDs, product codes, or rare technical words
that an embedding model might smooth over. Combining both, weighted,
covers more real questions correctly than either alone.

**Where BM25 comes from:** every chunk is also added to a keyword index
(`BM25SearchService.add_documents()`), tokenized by lowercasing and
splitting on whitespace, and persisted to disk as a pickled
`BM25Okapi` index (`storage/bm25/index.pkl`) plus a `documents.json`
sidecar. The index is **fully rebuilt** on every add or delete — it does
not update incrementally.

### How Reciprocal Rank Fusion (RRF) would differ

RRF is **not** what this project does — it's included here because it's
the other common way to combine two ranked lists, and worth knowing the
difference.

```
Vector results (ranked)      Keyword results (ranked)
         │                            │
         └──────────── RRF ───────────┘
                        │
              score(doc) = Σ 1 / (k + rank_in_list)
                        │
               Combined ranking
```

RRF combines results based on each item's **rank position** in each list
(not its raw score), which sidesteps the need to normalize two
differently-scaled scoring systems onto a comparable range. This project
instead normalizes the raw scores directly (`1/(1+distance)` for vector,
`score/max_score` for BM25) and combines them with fixed weights
(`vector_weight`, `bm25_weight` in `app/core/config.py`) — a valid,
simpler alternative to RRF, with the trade-off that the weights have to
be tuned by hand rather than being scale-independent by construction.

> **INDUSTRY ALTERNATIVES for hybrid retrieval:** Elasticsearch/OpenSearch
> (BM25 built in natively, vector search added via plugins/newer
> versions), Qdrant and Weaviate (both support hybrid search natively,
> often RRF-based), PostgreSQL full-text search combined with `pgvector`
> in the same database.

---

## 9. Relevance and Context Selection

**Reranking IS implemented** — `app/services/reranker.py`, class
`Reranker`:

```python
pairs = [[query, doc.content] for doc in documents]
scores = self.model.predict(pairs)   # cross-encoder/ms-marco-MiniLM-L-6-v2
for doc, score in zip(documents, scores):
    doc.rerank_score = 1 / (1 + math.exp(-float(score)))   # sigmoid → 0-1

ranked = sorted(documents, key=lambda x: x.rerank_score, reverse=True)
ranked = [d for d in ranked if d.rerank_score >= settings.reranker_score_threshold]  # 0.20
return ranked[:3]
```

**Why rerank at all, if hybrid search already ranked results:** the
embedding model scores a query against each chunk *independently* — fast
enough to run against thousands of chunks, but less precise. A
**cross-encoder** reads the query and one candidate chunk *together*,
which is far more accurate at judging true relevance, but too slow to run
against every chunk in a large collection. Running it only against the
top ~10 hybrid-search candidates is the standard "cheap shortlist, expensive
final pick" pattern.

**Score threshold:** `reranker_score_threshold = 0.20`. Anything below it
is dropped *before* the `[:3]` cut — so "nothing else is relevant enough"
can correctly mean fewer than 3 sources, or zero, instead of always
returning exactly 3 regardless of quality.

**Relevance shown to the user:** `SearchEvaluator.evaluate()`
(`app/services/search_evaluator.py`) grades the *best* remaining source's
score into a label:

```python
if best_score >= 0.7: quality = "Excellent"
elif best_score >= 0.5: quality = "Good"
else: quality = "Weak"
```

> **CURRENT:** cross-encoder reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`),
> score-threshold filtering, top-3 cap. Metadata filtering exists too —
> retrieval is always filtered `where={"document_id": ...}` to the
> requesting user's own documents (see section 12).

> **INDUSTRY ALTERNATIVES for reranking:** Cohere Rerank (hosted API),
> BGE reranker (`BAAI/bge-reranker-*`, open weights, similar approach to
> the cross-encoder used here), LLM-based reranking (asking an LLM
> directly to judge/order relevance — more expensive, sometimes more
> accurate for nuanced judgments).

---

## 10. Context Building

Three steps run in sequence on the reranked sources, all in
`RAGChatService.chat()`:

```
Reranked sources (top 3)
        ↓
ContextDeduplicator.remove_duplicates()   — drop exact-duplicate content
        ↓
ContextCompressor.compress()              — keep only sentences containing
        ↓                                     a question keyword; falls back
        ↓                                     to the full chunk if none match
ContextWindowManager.select_context()     — stop adding chunks once a
        ↓                                     word-count budget is hit
ContextFormatter.format()                 — build the final text block
```

**Deduplication** (`app/services/context_deduplicator.py`): compares each
source's `content.strip()` against a set of contents already seen; exact
matches are dropped.

**Compression** (`app/services/context_compressor.py`): splits each
chunk into sentences (`re.split(r'(?<=[.!?])\s+', content)`), keeps only
the sentences containing a word (>2 characters) from the question, and
replaces the chunk's content with just those sentences. For the running
example, given the question *"How many annual leave days do employees
receive?"*, keywords like `annual`, `leave`, `days`, `employees`,
`receive` would all match the one sentence in the chunk, so nothing is
trimmed away here — the full sentence survives.

**Context window** (`app/services/context_window_manager.py`): estimates
token count with `len(text.split())` (a simple word count, **not**
`tiktoken` — despite `tiktoken` being installed, a comment in this file
says "Later we can replace with tiktoken," and nothing in the codebase
actually imports it). Stops adding chunks once
`max_context_tokens (4000) - reserved_response_tokens (1000) = 3000` is
reached; nothing is truncated *within* a chunk, chunks are just dropped
once the budget runs out.

**Formatting** (`app/services/context_formatter.py`) builds the literal
text sent to the LLM:

```
SOURCE 1
--------------------

Document:
a1b2c3d4-....pdf

Chunk ID:
14-0

Similarity Score:
0.85

Content:
Employees receive 30 days of annual leave after completing one year of service.
```

Multiple sources are joined with `"\n\n"`. `PromptBuilder` explicitly
instructs the LLM not to repeat these `SOURCE`/`Chunk ID`/`Similarity
Score` labels in its answer — they're for the model's reference only (see
section 12).

**No truncation-within-a-chunk is implemented** — a chunk either
survives the token budget whole, or gets cut entirely by not being
included.

---

## 11. LLM Integration

```
User Question + Retrieved Context
        ↓
   PromptBuilder.build()
        ↓
   AIServiceRegistry.get_llm(provider).generate(prompt)
        ↓
   Generated Answer (text)
```

**SDK/library and model, by provider** — both implement the same
one-method interface, `app/services/llm/base.py`:

```python
class LLMService(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...
```

| Provider | File | SDK | Model | Configured by |
|---|---|---|---|---|
| Gemini | `app/services/llm/gemini.py` | `google-generativeai` | `gemini-3.6-flash` (`settings.gemini_model`) | `GEMINI_API_KEY`, `GEMINI_MODEL` env vars |
| Ollama | `app/services/llm/ollama.py` | `ollama` (Python client) | `llama3.1` (`settings.ollama_model`) | `OLLAMA_MODEL` env var; needs a reachable Ollama daemon |

```python
# GeminiService
genai.configure(api_key=settings.gemini_api_key)
self.model = genai.GenerativeModel(settings.gemini_model)
response = self.model.generate_content(prompt)
return response.text

# OllamaService
response = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
return response["message"]["content"]
```

**Which provider runs:** `AIServiceRegistry.get_llm(provider)`
(`app/core/ai_registry.py`) — `provider` comes from the request body's
optional `llm_provider` field (`ChatRequest.llm_provider`, set by the
frontend's Settings toggle); if not given, falls back to
`settings.llm_provider` (default `"ollama"`). Both clients are cached as
singletons per provider, so switching between them mid-session doesn't
reload either model.

**Error handling:** if `llm_provider="gemini"` is requested but
`GEMINI_API_KEY` isn't set, `get_llm()` raises `ValueError`, which
`app/api/chat.py` turns into a clean `400`. A `google.api_core.exceptions.GoogleAPIError`
raised during generation (e.g. hitting Gemini's free-tier quota) is
caught and turned into a `503` with Google's own error message — this is
a narrow catch; any other exception still surfaces as an unhandled `500`.
Ollama's client has no equivalent explicit error translation in this
codebase.

**Temperature / max tokens:** **not configured** anywhere in this
codebase — both `generate()` calls use each SDK's defaults. There is no
`temperature`, `top_p`, or `max_output_tokens` parameter set in
`GeminiService` or `OllamaService`.

**Fallback behavior:** none. If the configured provider fails, the
request fails — there is no automatic fallback to the other provider.

> **INDUSTRY ALTERNATIVES:** OpenAI, Anthropic (Claude), Azure OpenAI,
> AWS Bedrock (managed access to several model providers), self-hosted
> open-weight models (Llama, Mistral, etc., often served via vLLM or a
> similar inference server).

### RAG does not fine-tune the model

No training or fine-tuning happens anywhere in this pipeline. The LLM's
weights are never touched — every "customization" comes from what's put
in the prompt at request time:

```
Documents → Embeddings → Vector DB → Retrieve context → LLM generates from context
```

The model is the same general-purpose Gemini/Ollama model for every user
and every document; only the retrieved context changes.

---

## 12. Prompt Construction

**File:** `app/services/prompt_builder.py`, class `PromptBuilder`

```python
prompt = f"""
You are an AI assistant specialized in answering questions from provided documents.

Follow these rules strictly:

1. Answer only using the provided context.
2. Do not use external knowledge.
3. If the answer is not available in the context, respond exactly:
"I don't have enough information from the provided documents."
Do not add additional explanation.
4. Do not create or assume facts.
5. Keep the answer clear and concise.
6. The retrieved context below is labeled with internal metadata -
"SOURCE", "Document", "Chunk ID", "Similarity Score" - for your reference
only. Never repeat these labels, chunk IDs, filenames, or scores in your
answer. ...

Conversation History:
--------------------
{history_text}
--------------------

Retrieved Context:
--------------------
{context_text}
--------------------

User Question:
--------------------
{question}
--------------------

Answer:
"""
```

**Structure:** system instructions → conversation history → retrieved
context → the question, in that fixed order.

**Why context is inserted this way:** rule 1 ("answer only using the
provided context") plus rule 3 (an exact fallback sentence when the
answer isn't there) is the entire grounding mechanism — the model is
explicitly told not to use outside knowledge and given a specific
sentence to fall back to rather than guessing. Rule 6 exists because,
without it, a less strict-instruction-following model would sometimes
copy the `SOURCE`/`Chunk ID` labels verbatim into its answer instead of
writing natural prose (a real, observed bug — see
[`docs/sprints/09-rag-pipeline-and-hybrid-search.md`](sprints/09-rag-pipeline-and-hybrid-search.md)).

**Prompt injection / unrelated context:** **not specifically handled.**
There is no sanitization of retrieved chunk content before it's inserted
into the prompt — if an uploaded document itself contained adversarial
instructions, they would be inserted into the prompt as part of
"Retrieved Context" with no filtering. This is a real, unaddressed gap,
not a claimed protection (see [`docs/PRODUCTION_EVOLUTION.md`](PRODUCTION_EVOLUTION.md)).

---

## 13. Final Answer

```
LLM.generate(prompt) → answer text
        ↓
HallucinationGuardService.validate(question, context, answer)
        ↓ (if not grounded)
LLM.generate(strict_prompt) → regenerated answer
        ↓
RAGChatService returns a dict
        ↓
FastAPI serializes it (JSON, or word-by-word over SSE for /chat/stream)
        ↓
Client
```

**Hallucination guard** (`app/services/hallucination_guard_service.py`)
is a genuine second LLM call, not just a prompt instruction:

```python
prompt = f"""
You are a hallucination detection system.
Check whether the answer is fully supported by the provided context.
Return only JSON.
Question: {question}
Context: {context}
Answer: {answer}
Return: {{"grounded": true/false, "confidence": 0-1, "unsupported_claims": []}}
"""
response = self.llm_service.generate(prompt)
```

It strips a leading/trailing markdown code fence before `json.loads()`
(models — especially Gemini — sometimes wrap "JSON-only" responses in
` ```json ` anyway). If parsing still fails, it defaults to
`{"grounded": False, "confidence": 0, "unsupported_claims": ["Unable to
validate response"]}` — a parse failure is treated as "not grounded,"
not as "skip the check."

If `grounded` is `False`, `RAGChatService` builds a stricter prompt
(`_build_strict_prompt`, same rules, more terse) and calls
`LLM.generate()` a **third** time. This means a single user question can
trigger up to **3 LLM calls just for generation and validation** (plus
2 more for query rewriting/expansion beforehand — 5 total in the worst
case).

**What prevents the LLM from answering without context:** nothing at the
network/code level prevents it from trying — the protection is entirely
the prompt rules (section 12) plus this validation pass. If retrieval
returns zero documents at all, `RAGChatService.chat()` short-circuits
before ever calling the LLM and returns a canned *"I don't have enough
information."* directly (no LLM call happens in that specific case).

**Response shape** (`RAGChatService.chat()`'s return value):

```json
{
  "conversation_id": "uuid",
  "question": "How many annual leave days do employees receive?",
  "answer": "Employees receive 30 days of annual leave after completing one year of service.",
  "sources": [ { "document_id": "14", "chunk_id": "14-0", "filename": "...", "content": "...", "score": 0.85, "rerank_score": 0.91 } ],
  "search_evaluation": { "quality": "Excellent", "best_score": 0.85, "average_score": 0.85, "retrieved": 1 },
  "evaluation": { "quality": "Good", "best_score": 0.85, "average_score": 0.85 }
}
```

`POST /chat` returns this as one JSON response. `POST /chat/stream`
(`app/api/chat.py`) runs the exact same pipeline to completion first,
then reveals `answer` word-by-word as Server-Sent Events, followed by a
final event carrying `sources`/`search_evaluation`/`conversation_id` —
this is a presentation-layer effect, not token-level LLM streaming (the
hallucination guard has already finished validating before the first
word is sent).
