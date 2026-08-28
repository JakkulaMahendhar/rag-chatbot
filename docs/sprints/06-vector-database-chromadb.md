# Sprint 6 — Vector Database Integration (ChromaDB)

## Objective

Sprint 5 gave us a way to turn text into vectors. Now we need somewhere to
*store* thousands of these vectors and *search* them efficiently — "given
this query vector, find the 5 most similar stored vectors" — which is not
something a regular relational database does natively or fast.

## What we built

**File:** `app/services/vector_store.py`

```python
class VectorStoreService:
    def __init__(self):
        self.client = ChromaClient.get_client()
        self.collection = self.client.get_or_create_collection(name="documents")

    def add_chunks(self, chunks, embeddings):
        self.collection.upsert(
            ids=[str(chunk.chunk_id) for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=[e.embedding for e in embeddings],
            metadatas=[chunk.metadata for chunk in chunks],
        )

    def search(self, query_embedding, top_k=3, document_ids=None):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"document_id": document_ids[0]} if document_ids else None,
        )
        # returns chunks ranked by distance (lower = more similar)
```

## Why ChromaDB specifically

Real alternatives considered implicitly by the shape of this decision:
storing raw vectors in Postgres columns and computing similarity manually
in Python (extremely slow at any real scale — no index structure), or using
a heavier dedicated vector database (Pinecone, Weaviate) which would add
external service dependency and cost for a project this size. ChromaDB
hits a sweet spot: purpose-built for exactly this (fast approximate nearest
neighbor search via an HNSW index), and can run either embedded (simple) or
as its own server (for production, see below).

## A real architectural evolution — this changed mid-project

**Originally** (this sprint), ChromaDB ran *embedded* —
`chromadb.PersistentClient(path=...)` directly inside the web app process,
reading/writing files on local disk. This is the simplest possible setup
and worked fine for a single-process application.

**Later** (Sprint 12), this became a real, reproduced bug: once the
application was split into a separate web process and worker process (for
the async upload pipeline), both processes were independently opening
embedded ChromaDB storage handles against the *same* directory. ChromaDB's
embedded client isn't designed for concurrent multi-process access — this
produced a genuine, repeatedly-reproduced error:
`chromadb.errors.InternalError: Error executing plan: Internal error: Error finding id`.

The fix (documented in full in Sprint 12's doc): ChromaDB now runs as its
**own server** (a separate Docker container, `chromadb/chroma:1.5.9`), and
both the web app and worker connect to it over HTTP via
`chromadb.HttpClient` instead of touching the storage directly. This is
exactly the kind of thing that only surfaces once you actually run the
real multi-process architecture — good to know if you build a similar
system starting from a single-process design.

## How it works — a real walkthrough

Given a stored chunk with embedding `[-0.0869, -0.0369, ...]` and metadata
`{"document_id": "14", "user_id": "7", ...}`:

1. `add_chunks()` calls `collection.upsert()` — ChromaDB stores the vector,
   the original text, and the metadata together, indexed for fast search.
2. Later, a user asks a question. The question itself gets embedded
   (Sprint 5's `generate_query_embedding()`), producing a query vector.
3. `collection.query(query_embeddings=[query_vector], n_results=3)` asks
   ChromaDB: "of everything stored, which 3 vectors are closest to this
   one?" — using L2 (Euclidean) distance under the hood.
4. Results come back **ranked by distance, lowest first** — this exact
   detail matters and caused a real, documented frontend bug (see Sprint
   13/frontend doc and the bugs doc): the raw distance is *not* a 0-100%
   similarity score, and a naive `score * 100` display was actively
   misleading before being caught and fixed.
5. The `where={"document_id": ...}` filter is what makes per-user document
   scoping possible — search results are filtered to only chunks belonging
   to documents the requesting user actually owns (see Sprint 10).

## Positive scenarios

- Verified via direct testing in this project: a document containing the
  text "Artificial Intelligence (AI) is a branch of computer science..."
  correctly returns as the top result for the query "What is Artificial
  Intelligence?" with the closest vector distance among all stored chunks.
- The HttpClient migration was stress-tested with the tightest realistic
  race condition (a search request fired the instant the worker was
  writing a new vector) and held up correctly — no errors, correct ranked
  results for both the new and existing documents.

## Negative scenarios / limitations

- **The original embedded-client architecture had a real, reproducible
  concurrency bug** (detailed above and in the bugs doc) — worth knowing if
  you ever see "Error finding id" from ChromaDB: it's very likely a
  multi-process access issue, not data corruption.
- **No persistent disk on Render's free tier** (see Sprint 12) means the
  entire vector index is wiped on every redeploy or scale-to-zero cold
  start in the current free-tier production deployment — a real, currently
  unresolved production limitation, not fixed as of this writing.
- Distance-based filtering (`vector_distance_threshold` in config) is a
  single global cutoff — it doesn't adapt per query or per document type,
  so it can be either too permissive (irrelevant results) or too strict
  (missing relevant-but-differently-worded content) depending on the
  specific question.
