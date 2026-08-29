# Sprint 12 — Deployment, Background Worker Queue, and Running ChromaDB as a Server

## The example at this step

This sprint takes the app live on Render, and specifically makes sure that
when Sarah uploads `Employee_Leave_Policy.pdf` in production, the upload
returns quickly instead of timing out, and that the background process
turning it into searchable chunks doesn't corrupt anything while the web
app is also running.

## Part 1 — Why the app needs to run in the background at all

**File:** `app/api/upload.py`, `app/worker.py`,
`app/services/document_registration_service.py`

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `POST /upload` (fast path) | Saves the file and creates a `Document` row with `status="pending"`, then returns immediately | Parsing, chunking, and embedding a document can take 40+ seconds for a large file — doing all of that inside the same HTTP request Sarah's browser is waiting on risks a timeout | Doing everything synchronously in one request is simpler to write, but ties up the request (and the server's memory) for as long as the slowest document takes |
| `app/worker.py` (separate process) | Polls Postgres every 5 seconds for documents with `status="pending"`, and does the actual parsing/chunking/embedding | Runs independently of the web app, so a slow document doesn't block Sarah's (or anyone else's) next request from being handled | — |

```python
# app/api/upload.py - fast, "register only"
document = await service.register(file=file, user_id=current_user.id)
return UploadResponse(status=document.status, ...)   # returns 202, status="pending"

# app/worker.py - separate process, polls for pending work
async def run():
    while True:
        pending = await repository.get_pending_documents(limit=5)
        for document in pending:
            await processing_service.process_document(document)
        await asyncio.sleep(5)
```

A background worker fixes the *timeout* problem. It doesn't, by itself,
reduce how much memory embedding actually needs — it just lets that work
run in a process whose memory can be sized independently of the
web-facing service.

## Part 2 — Why ChromaDB runs as its own server, not embedded in the app

**File:** `app/services/chroma_client.py`, `app/services/vector_store.py`

Sprint 6 originally ran ChromaDB *embedded* — directly inside the web
app's process, reading and writing files on local disk. That worked fine
with one process. Once the worker (Part 1, above) became a **second**,
separate process also touching the same document data, both processes
were independently opening embedded ChromaDB storage against the same
directory — something ChromaDB's embedded client isn't designed for.

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `chromadb.HttpClient` | Both the web app and the worker connect to ChromaDB over HTTP, instead of opening its storage files directly | A single ChromaDB **server** (its own container) is the one place actually touching the storage, so there's no race between two processes writing to the same files at once — the exact scenario that happens when the worker is embedding Sarah's document while the web app is simultaneously handling someone else's search | The embedded `PersistentClient` is simpler to set up, but only safe with one process; running the worker as a separate process specifically requires this change |

```python
# app/services/chroma_client.py
cls._client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)

# app/services/vector_store.py — uses the singleton, not a fresh client per call
self.client = ChromaClient.get_client()
```

## Part 3 — Deploying to Render

**File:** `render.yaml`

| Piece | What it does | Why we used it |
|---|---|---|
| Web service (`type: web`) | Serves Sarah's upload and chat requests | The public-facing part of the app |
| Worker service (`type: worker`) | Runs `app/worker.py`, processing `Employee_Leave_Policy.pdf` in the background after Sarah uploads it | Separated so its memory needs can be sized independently of the web service, per Part 1 |
| Managed Postgres | Stores Sarah's account and document metadata | Render-managed, so backups and connection details are handled outside the app |

## How it works — Sarah's upload, in production, end to end

1. Sarah uploads `Employee_Leave_Policy.pdf` through the deployed frontend.
2. The web service saves the file, creates a `Document` row with
   `status="pending"`, and responds immediately — Sarah's browser doesn't
   wait for parsing or embedding.
3. The worker service, polling every 5 seconds, picks up the pending
   document, parses it (Sprint 3), chunks it (Sprint 4), embeds it
   (Sprint 5), and writes the vectors to the ChromaDB **server** over HTTP
   (Part 2, above) — not by touching files directly.
4. The `Document` row's status flips to `"completed"`, which the frontend
   (Sprint 13) is polling for, so Sarah sees her document go from
   "Processing..." to ready.
5. When Sarah then asks her sick-leave question, the web service (a
   different process from the worker) queries the same ChromaDB server
   over HTTP and finds the chunk the worker wrote — safely, because both
   processes only ever talk to ChromaDB through the same server, never
   through the same files directly.

See [14-bugs-and-lessons-learned.md](14-bugs-and-lessons-learned.md) for
the real memory-crisis and concurrency bugs found while getting this exact
flow working, and how each was actually diagnosed and fixed.
