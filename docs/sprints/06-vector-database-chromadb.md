# Sprint 6 — Vector Database Integration (ChromaDB)

## The example at this step

The sick-leave chunk now exists as a 384-number vector
(`[-0.0869, -0.0369, ...]`). It needs somewhere to actually live, and a way
to be found again later when Sarah asks her question — "given this new
vector, find the stored vectors closest to it" — which a regular
relational database doesn't do natively or fast.

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
```

## Classes & libraries used, and why

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| **ChromaDB** | Stores vectors alongside their original text and metadata, and answers "which stored vectors are closest to this one?" using an HNSW index | Purpose-built for exactly this — fast approximate nearest-neighbor search — and can run either embedded (simple, single-process) or as its own server | Storing vectors as Postgres columns and comparing them by hand in Python has no real index structure and gets slow as the number of chunks grows; a heavier managed vector database (Pinecone, Weaviate) would add an external paid dependency this project doesn't need |
| `VectorStoreService.add_chunks()` | Writes a chunk's text, vector, and metadata into ChromaDB together in one call | One call stores everything needed to both find the chunk later *and* show Sarah where the answer came from | Storing the vector and the original text/metadata separately would need two round trips and a way to keep them in sync |
| `collection.query(...)` | Given a query vector, returns the closest stored vectors, ranked by distance | This is the exact operation "find the chunk most similar in meaning to Sarah's question" needs | — |
| `chromadb.HttpClient` (server mode) | Both the web app and the background worker connect to ChromaDB over HTTP instead of opening the storage files directly | Once there are two separate processes (web + worker, Sprint 12) touching the same data, they need to go through one server rather than both opening the same files on disk | The simpler embedded mode (`PersistentClient`, opening files directly) works fine for a single process, but breaks once a second process needs to write at the same time — see Sprint 12 for the real bug this caused |

## How it works — storing and finding Sarah's chunk

1. `add_chunks()` calls `collection.upsert()` for chunk `"14-1"`: ChromaDB
   stores its vector, its original text (*"All full-time employees are
   entitled to 12 paid sick leaves..."*), and its metadata
   (`{"document_id": "14", "user_id": "7", ...}`) together, indexed for
   fast search.
2. Weeks later, Sarah asks: *"How many sick leaves do I get per year?"*
   Her question is embedded the same way (Sprint 5), producing a query
   vector.
3. `collection.query(query_embeddings=[query_vector], n_results=3)` asks
   ChromaDB: "of everything stored for Sarah's documents, which 3 vectors
   are closest to this one?" — using L2 (Euclidean) distance under the
   hood.
4. Chunk `"14-1"` comes back as the closest match, because its vector was
   already numerically close to any vector representing "how much sick
   leave do I have" — the model doesn't need Sarah to use the document's
   exact wording.
5. The `where={"document_id": ...}` filter is what makes per-user scoping
   possible — Sarah's search is restricted to only the chunks belonging to
   documents she actually owns (Sprint 10).

Results come back ranked by **distance** (lower = closer, i.e. more
similar) — not a 0–100% score. That distance value is converted into
something human-readable for display in Sprint 9 and reused as-is by the
frontend in Sprint 13, so it's only ever calculated in one place.

## A real bug: the Docker volume was never actually being used

`docker-compose.yml` mounts a named volume at `/chroma/chroma`, meant to
keep every uploaded document's vectors around across restarts. It looked
correct, `docker compose down`/`up` never complained, and searches worked
fine — right up until retrieval quality quietly degraded (weak match
scores, and the hallucination guard genuinely triggering on questions
that used to answer fine). Inspecting the collection directly
(`scripts/inspect_chroma.py`) showed **1 total vector**, when it should
have had hundreds.

The actual cause, found by reading the chroma container's own startup
log: `persist_path: "/data"`. The `chromadb/chroma:1.5.9` image ships a
config file baked in at `/config.yaml` that hardcodes `/data` as where it
saves data — a completely different path from `/chroma/chroma`, which is
where the volume was mounted. Chroma had been writing every vector to the
container's own disposable filesystem layer this entire time; the volume
mount was a no-op. Every time the container got recreated — any
`docker compose down`/`up`, any `--build` — all vector data was silently
thrown away, while Postgres (mounted correctly) kept everything. Postgres
still listed old documents as `status: "completed"`; their actual
retrievable content was gone.

**The fix:** `chroma run` refuses to combine its config-file argument with
`--path`/`--host` flags (confirmed directly against the image — it errors
out immediately), so the config file is dropped entirely in favor of
explicit flags that match where the volume actually is:

```yaml
# docker-compose.yml
command: ["run", "--path", "/chroma/chroma", "--host", "0.0.0.0"]
```

**Verified properly, not just with a restart:** a plain container
*restart* would have looked fine even under the old broken setup, since
the same container's disposable layer survives a restart — that's not a
real test. The real test is a full recreation: uploaded a document,
ran `docker compose up -d --force-recreate chroma`, and confirmed the
chunk count survived. It did.

**Real-world consequence:** any document uploaded before this fix has a
Postgres row saying `"completed"` but no actual content left in Chroma —
those documents need to be deleted and re-uploaded; there's nothing to
recover.
