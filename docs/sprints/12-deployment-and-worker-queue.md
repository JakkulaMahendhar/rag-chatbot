# Sprint 12 — Deployment, Background Worker Queue, and the ChromaDB Concurrency Bug

## Objective

Get the application actually running on the public internet (Render), not
just locally — and along the way, this sprint surfaced (and fixed) the most
significant real architectural bugs found in the entire project. This file
documents that journey honestly, including the mistakes and dead ends, not
just the final working state.

## Part 1 — Initial deployment attempt and the memory crisis

**File:** `render.yaml` — a Blueprint defining the web service against a
managed Postgres.

### The first real production failure: Out Of Memory

The very first deploy attempt failed with the deploy log literally showing:
`==> Out of memory (used over 512Mi)`. Root cause, confirmed by research:
Render's free/Starter web service plans are **both** capped at 512MB RAM
(a real, verified fact — Starter, the $7/mo paid tier, does *not* increase
RAM, only Standard at $25/mo does). The application was loading PyTorch +
the embedding model *eagerly* at process startup (`app/main.py`'s lifespan
handler), which alone exceeded the ceiling before the server could even
start.

### The fix, in three real, escalating attempts

1. **First attempt:** stop calling `AIServiceRegistry.get_embedding_model()`
   at startup — defer it to first actual use. This alone was **not
   enough** — the deploy still failed, this time with
   `"Port scan timeout reached, no open ports detected"` (a *different*
   failure than OOM).
2. **Diagnosis:** removing the eager *call* didn't remove the eager
   *import*. `sentence_transformers` (and therefore `torch`) was still
   imported at the top of `ai_registry.py`, and Python evaluates all
   top-level imports the moment a module is imported — so the heavy
   import happened at boot regardless of whether the model was ever
   loaded.
3. **Real, bisected root cause:** by systematically importing each router
   one at a time and checking `sys.modules`, the actual culprit was
   isolated to **`app/services/chunker.py`**'s
   `from langchain_text_splitters import RecursiveCharacterTextSplitter` —
   confirmed, surprisingly, that this single import alone pulls in
   `torch`/`transformers`/`sentence_transformers` (~3,900 modules),
   regardless of which specific splitter class is used, because the
   package's own `__init__.py` re-exports tokenizer-based splitters too.
4. **Final fix:** moved the imports in `ai_registry.py`, `reranker.py`, and
   `chunker.py` from module top-level to *inside* their respective
   methods/`__init__`. Verified directly by checking `sys.modules` after
   importing `app.main` — genuinely zero heavy ML modules loaded at boot
   after the fix.

This whole sequence — three distinct failure modes, each requiring real
diagnosis, not guessing — is a genuine example of how "defer the import"
sounds simple but has layers.

## Part 2 — Background worker queue

**File:** `app/worker.py`, `app/services/document_registration_service.py`

### Why this was needed

The synchronous `/upload` endpoint (do everything in one HTTP request) was
the exact code path that had been OOMing. Beyond memory, it also risked
request timeouts on large documents (parsing + chunking + embedding all in
one request, sometimes 40+ seconds).

### The real architecture

```python
# app/api/upload.py - now fast, "register only"
document = await service.register(file=file, user_id=current_user.id)
return UploadResponse(status=document.status, ...)   # returns 202, status="pending"

# app/worker.py - separate process, polls for pending work
async def run():
    while True:
        pending = await repository.get_pending_documents(limit=5)
        for document in pending:
            await processing_service.process_document(document)   # the actual heavy work
        await asyncio.sleep(5)
```

**Important, explicitly documented finding:** a worker queue fixes the
*timeout* problem. It does **not**, by itself, fix the *memory ceiling*
problem — the actual embedding/chunking work still needs to run
*somewhere* with enough RAM. Moving it to a separate process just lets you
size that process's memory independently of the web-facing service.

### A real race condition found while building this

Running two separate processes (`entrypoint.sh` for the web app,
`worker_entrypoint.sh` for the worker) both running `alembic upgrade head`
on startup **looked** idempotent (running the same migration command twice
is normally safe) but wasn't, under concurrency: Docker Compose starts both
containers as soon as the database is healthy, so both attempted the same
`ALTER TABLE` simultaneously. Postgres serialized them at the lock level —
the second one blocked, then failed with `"column already exists"` once
unblocked, because the first had already committed by then. Fixed by
running migrations from *only* the web service's entrypoint; the worker's
poll loop already tolerates the table not existing yet (wrapped in a
try/except that retries the next cycle).

## Part 3 — The ChromaDB concurrency bug (found via real production testing, not anticipated)

This is arguably the most instructive bug in this entire project.

### The symptom

`chromadb.errors.InternalError: Error executing plan: Internal error: Error finding id`
— appearing intermittently on `/chat` and `/search` requests.

### Why it was hard to diagnose initially

The first two times this appeared, it happened after extensive manual
testing (many uploads, deletes, container restarts) — it was reasonable to
initially suspect "accumulated test-session corruption," and a full volume
wipe + restart did make it go away temporarily, reinforcing that
hypothesis.

### The real breakthrough

The bug reappeared on a **completely fresh install** — every Docker volume
including Postgres wiped, a single document uploaded, one chat message
sent. This single reproduction on minimal state definitively ruled out
"accumulated test mess" and confirmed a genuine architectural bug.

### Root cause, confirmed by reading the actual code

`VectorStoreService.__init__` created a **brand new**
`chromadb.PersistentClient(path=...)` on *every single instantiation* —
notably, bypassing an already-existing `ChromaClient` singleton wrapper
that was never actually used. Combined with the Part 2 worker split (now
two separate OS processes, not one), both processes were independently
opening embedded, file-backed storage handles against the same directory.
ChromaDB's embedded client is not designed for concurrent multi-process
access.

### The fix

Run ChromaDB as its **own server** (`chromadb/chroma:1.5.9`, exactly
version-matched to the installed Python client), both the web app and
worker connect via `chromadb.HttpClient` over the network instead of
touching storage directly:

```python
# app/services/chroma_client.py
cls._client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)

# app/services/vector_store.py — now actually uses the singleton
self.client = ChromaClient.get_client()
```

A real, non-obvious detail hit while building this: the Chroma server's
official Docker image ships **neither curl, wget, nor Python** — a
standard container healthcheck using any of those tools would silently
never work. Confirmed by directly inspecting the running container.
Fixed with a healthcheck using only `bash`'s built-in `/dev/tcp`
pseudo-device (verified `bash` was present; also had to explicitly invoke
`bash` rather than rely on Docker's default `CMD-SHELL`, which runs via
`/bin/sh` — confirmed to be `dash` in this image, which doesn't support
`/dev/tcp` at all).

### Verification — not just "it built successfully"

The fix was stress-tested with the *tightest* realistic reproduction: a
search request fired the instant a second document upload was being
written by the worker — the exact race window that would have failed
before. It succeeded, correctly returning both documents, ranked. This was
the actual bar for calling the fix "confirmed," not just "the app started
without errors."

## Positive scenarios

- The final architecture (web + worker + Chroma server + Postgres, all
  containerized) genuinely survives the exact concurrency conditions that
  broke the earlier, simpler design — verified under real stress, not
  assumed.
- Docker Compose locally now matches what's intended for production
  closely enough that this exact bug was findable and fixable *before* it
  became a mystery production incident with no local reproduction.

## Negative scenarios / limitations (as of this writing)

- **Render's free tier has no persistent disk** — even with the
  architecture fixed, uploaded documents, the vector index, and the BM25
  index do **not** survive a redeploy or scale-to-zero cold start on the
  free plan. This is a known, accepted, unresolved tradeoff for staying
  free, documented explicitly in `render.yaml`'s own comments.
- **`render.yaml` has not yet been updated to include a Chroma server for
  the actual Render deployment** — the fix above was implemented and
  verified in `docker-compose.yml` (local), but as of this writing,
  production Render deployment would still fail on chat/search, since the
  web app has no `CHROMA_HOST` configured there.
- **A real, unresolved cost decision remains:** getting the complete flow
  working in production requires paying for both a worker with enough RAM
  (Standard plan, ~$25/mo — Starter's 512MB doesn't fix the original OOM)
  and a Chroma private service (no free tier for private services, ~$7-10/mo
  including a persistent disk) — roughly $32-35/mo additional cost,
  explicitly not yet committed to as of this writing.
