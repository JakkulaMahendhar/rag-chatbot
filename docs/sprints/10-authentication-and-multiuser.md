# Sprint 10 — Authentication, PostgreSQL & Multi-User Document Ownership

## The example at this step

Everything so far assumed a single implicit user. This sprint makes sure
that when a second Acme Corp employee — say, **Raj** — logs in, he can
never see, search, or delete Sarah's `Employee_Leave_Policy.pdf`, even
though they're using the same running system.

## What we built

**File:** `app/database/models/user.py`, `app/database/models/document.py`
— real Postgres tables via SQLAlchemy (async), versioned by Alembic.

**File:** `app/auth/jwt.py`:
```python
def create_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)  # 30 min
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

**File:** `app/database/repositories/document_repository.py` — every
document query is scoped by `user_id`:
```python
async def get_by_id_and_user(self, document_id, user_id):
    result = await self.session.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    return result.scalar_one_or_none()   # None if it exists but belongs to someone else
```

## Classes & libraries used, and why

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| **JWT** (`python-jose`) | A signed, self-contained token proving "this request is really Sarah," valid for 30 minutes | The frontend and backend are genuinely separate deployments — a stateless token that verifies itself needs no shared session store between them, or between the web app and the worker process | Server-side session cookies would need every backend instance to share session state somewhere, which adds infrastructure this project's shape doesn't need |
| `get_by_id_and_user(document_id, user_id)` | Every document lookup filters by *both* the document ID *and* the requesting user's ID in a single query | This is the actual mechanism that stops Raj from ever retrieving Sarah's document — even if he guesses her document's ID correctly, the query returns nothing because the `user_id` doesn't match | Checking "does this document exist?" and "does it belong to this user?" as two separate steps would create a window where the first check leaks whether the ID exists at all |
| Returning **403**, not 404, when a document doesn't exist *or* belongs to someone else | The API gives the exact same response either way | If Raj tried document ID 999 (doesn't exist) and got 404, but tried Sarah's real document ID and got 403, he could enumerate which document IDs are real just by watching the status code — a real information-leak class. One consistent 403 closes that | Returning 404 for "doesn't exist" and 403 for "exists but not yours" is more conventional REST practice, but leaks exactly the information this system is trying to protect |
| **bcrypt** (via `passlib`) | Hashes Sarah's password before storing it, deliberately slowly | Slow hashing is a *feature* here — it makes brute-forcing a stolen password hash expensive | Fast hashes (like plain SHA-256) are wrong for passwords specifically — an attacker with the hash could try billions of guesses per second |
| `InMemoryRateLimiter` | Limits `/auth/register` and `/auth/login` to 5 attempts per 60 seconds, per IP | Slows down password-guessing attacks against real accounts like Sarah's | A distributed rate limiter (e.g. Redis-backed) would enforce one true global limit across multiple processes; this in-memory version is a lighter, single-process-scoped version of the same idea — documented in its own code as such |

## How it works — Sarah and Raj, side by side

1. Sarah registers: `POST /auth/register` with her email + password.
   Her password is hashed with bcrypt; a `User` row is created in
   Postgres.
2. `POST /auth/login` verifies her password against the stored hash and
   returns a JWT valid for 30 minutes.
3. Every request after that — including `POST /upload` for
   `Employee_Leave_Policy.pdf` — includes `Authorization: Bearer <token>`.
   `get_current_user` decodes it and attaches Sarah's identity to the
   request.
4. When Sarah uploads her PDF, the resulting `Document` row is saved with
   `user_id = Sarah's ID`.
5. If Raj — a separate, independently registered user — tries
   `GET /documents/14` (Sarah's document), `get_by_id_and_user(14,
   raj_id)` finds a document with ID 14, but its `user_id` doesn't match
   Raj's ID, so the query returns nothing and the API responds `403`.
6. When Sarah asks her sick-leave question, `POST /chat` passes
   `current_user.id` down into retrieval (Sprint 6/7), so ChromaDB is
   searched only within documents she owns — Raj's own uploads, if any,
   are never in scope for her search, and vice versa.
