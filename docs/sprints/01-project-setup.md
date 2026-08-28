# Sprint 1 — Project Setup

## Objective

Before writing any AI/RAG logic, establish a backend skeleton that won't need
to be restructured later as the project grows. Getting this wrong early
(e.g., putting everything in one file) creates painful refactors later.

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

**Real file that started it all:** `app/main.py` — even in its very first
version, it did nothing but:
```python
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to AI Knowledge Assistant"}
```

## Why this structure specifically

This follows a layered architecture, enforcing **separation of concerns**:

- **`api/`** should only know about HTTP (status codes, request parsing). It
  should never contain business logic like "how do we chunk a document."
- **`services/`** contains the actual logic and has no idea it's being called
  from an HTTP request — it could just as easily be called from a CLI script
  or a background worker (this exact property is what made Sprint 12's
  worker-queue split possible later *without rewriting the processing logic*
  — `DocumentProcessingService` didn't need to change internally, it just
  moved to being called from `app/worker.py` instead of an API route).
- **`schemas/` vs `models/`** — a deliberate split: `schemas/` is what the
  *outside world* (API clients) sees; `models/` is internal data passed
  between services. This means we can change internal data shapes without
  breaking the API contract, and vice versa.

## Real example of why this paid off later

When Sprint 10 added authentication, **zero changes were needed** to
`app/services/parser.py` or `app/services/chunker.py` — auth was added
entirely in a new `app/auth/` module and wired in via FastAPI's dependency
injection (`Depends(get_current_user)`) at the API layer. The business logic
never had to know a user system existed.

## Positive scenarios (what worked well)

- The structure scaled from a single `/` endpoint (Sprint 1) to 6 full
  routers (`upload`, `documents`, `auth`, `chat`, `search`, `health`) by
  Sprint 10 without ever needing a "big refactor."
- New engineers (or, in this case, an AI assistant picking this project back
  up in a later session) can predict where to find code: "how does chunking
  work?" → `app/services/chunker.py`, no searching required.

## Negative scenarios / honest limitations

- One real inconsistency that persisted: `app/models/` accumulated both
  genuinely-internal models (`app/models/chunk.py`) *and* some that are
  really API-shaped (`app/models/search.py`'s `SearchResult` is returned
  directly by an endpoint). The `schemas/` vs `models/` boundary wasn't
  enforced with 100% discipline throughout the project — a minor,
  non-breaking architectural drift worth knowing about if extending this
  codebase.
- There's no `tests/` subfolder mirroring the `app/` structure 1:1 (e.g.
  `tests/services/test_chunker.py`) — tests live flat in `tests/`. Fine at
  this project's current size, would need reorganizing if it grew much
  larger.
