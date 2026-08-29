# Sprint 1 — Project Setup

## The example at this step

Before Sarah can upload anything, the backend needs a folder structure that
won't need to be torn apart every time a new feature (auth, a worker,
hybrid search) gets added. This file explains that structure using the
question: *when Sarah's upload request arrives, which files does it pass
through, and why is the project organized that way?*

## What we built

```
app/
├── main.py       # FastAPI app instance, router registration
├── api/          # HTTP layer - request/response handling only
├── services/     # Business logic - the actual "how do we do X"
├── models/       # Internal data shapes (Pydantic models used between layers)
├── schemas/      # API-facing data shapes (request/response contracts)
├── core/         # Cross-cutting concerns: config, logging, exceptions
└── database/     # ORM models, repositories, DB session management
```

## The layers, what each one does, and why it exists

| Layer | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `api/` | Reads Sarah's HTTP request, calls a service, returns an HTTP response | Keeps HTTP concerns (status codes, request parsing) completely separate from business logic | Putting `chunk_text()` logic directly inside a route handler works at first, but makes it impossible to reuse that logic from a background worker later without duplicating it |
| `services/` | Contains the actual logic — parsing, chunking, embedding, retrieval | A service has no idea it's being called from an HTTP request; it just takes data and returns data | This is exactly what let Sprint 12 move document processing into a background worker: `DocumentProcessingService` didn't change internally, it just got called from `app/worker.py` instead of `app/api/upload.py` |
| `schemas/` | What the *outside world* (Sarah's browser) sends and receives — request/response contracts | Lets internal data shapes change without breaking the API, and vice versa | Reusing one Pydantic model for both "what the API returns" and "what's passed between services" means an internal refactor can accidentally change the public API contract |
| `models/` | Internal data shapes passed between services (e.g. a parsed chunk before it has an ID) | Keeps internal representations free to evolve independently of what the API promises | Same reasoning as above, from the other direction |
| `core/` | Settings, logging, shared exceptions | One place for anything every layer needs, instead of scattering config reads through the codebase | Hardcoding a value like `chunk_size` inside `chunker.py` directly means changing it later means hunting through files instead of editing one `Settings` class (Sprint 7) |
| `database/` | SQLAlchemy models, repositories, session management | Isolates *how* data is stored (Postgres, SQLAlchemy) from *what* the rest of the app needs (a `Document` object) | Without this layer, a database schema change would ripple directly into business logic instead of stopping at the repository |

## How it works — Sarah's request, layer by layer

1. Sarah's browser sends `POST /upload` with `Employee_Leave_Policy.pdf`.
2. `app/api/upload.py` (the API layer) receives the HTTP request, checks
   the file extension, and calls `StorageService` and
   `DocumentRegistrationService` (the service layer) — it never touches a
   database directly.
3. Those services use `app/database/repositories/document_repository.py`
   to write a `Document` row for Sarah, without knowing or caring that the
   request came from HTTP — the exact same service could be called from a
   script or a worker.
4. The response sent back to Sarah's browser is shaped by
   `app/schemas/upload.py`, not by whatever internal object the service
   happened to use.

## Why this paid off concretely, later in the project

When Sprint 10 added authentication, **zero changes were needed** in
`app/services/parser.py` or `app/services/chunker.py` — auth was added
entirely in a new `app/auth/` module and wired in via FastAPI's dependency
injection (`Depends(get_current_user)`) at the API layer only. The parsing
and chunking logic never had to know a user system existed. The same
layering is what let the project grow from a single `/` endpoint to six
full routers (`upload`, `documents`, `auth`, `chat`, `search`, `health`)
without a rewrite.
