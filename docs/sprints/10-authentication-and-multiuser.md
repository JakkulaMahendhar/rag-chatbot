# Sprint 10 — Authentication, PostgreSQL & Multi-User Document Ownership

## Objective

Everything built so far worked for a single, implicit "everyone shares
everything" user. This sprint made the system genuinely multi-tenant: real
user accounts, real passwords, and — critically — making sure User A can
never see or search User B's uploaded documents.

## What we built

**File:** `app/database/models/user.py`, `app/database/models/document.py`
— real Postgres tables via SQLAlchemy (async), with migrations managed by
Alembic (`migrations/versions/`).

**File:** `app/auth/jwt.py`:
```python
def create_access_token(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)  # 30 min
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
```

**File:** `app/auth/security.py` — password hashing via `passlib` + `bcrypt`.

**File:** `app/database/repositories/document_repository.py` — every query
is scoped by `user_id`:
```python
async def get_by_id_and_user(self, document_id, user_id):
    result = await self.session.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    return result.scalar_one_or_none()   # None if it exists but belongs to someone else
```

## Why JWT (stateless tokens), not server-side sessions

Real, concrete reason confirmed by this project's own later architecture:
the frontend (Sprint 13) and backend are genuinely separate deployments —
different processes, potentially different hosts. A stateless bearer token
(the JWT) means any request carrying a valid token can be verified without
the server needing to look up session state anywhere — no shared session
store needed between multiple backend instances either, which matters once
you have a worker process too (Sprint 12).

## Why `403`, not `404`, when a document doesn't exist OR belongs to someone else

A real, deliberate security decision, confirmed in `app/services/document_service.py`:

```python
document = await self.repository.get_by_id_and_user(document_id, user_id)
if not document:
    raise HTTPException(status_code=403, detail="You don't have permission...")
```

The API returns the **exact same response** whether document ID 999 simply
doesn't exist, or exists but belongs to another user. This is deliberate:
if the API distinguished "404 not found" from "403 forbidden," an attacker
could enumerate valid document IDs belonging to other users just by
watching which status code comes back — a real, known class of information-
leak vulnerability, closed here by design.

## Why bcrypt for password hashing (and a real bug this caused)

bcrypt is a well-established, deliberately slow hashing algorithm (slow is
a *feature* for password hashing — it makes brute-forcing expensive).

**A real, confirmed, reproduced bug found in this exact project:**
upgrading `bcrypt` to version `5.0.0` broke password hashing **entirely** —
every single registration/login attempt failed with
`"password cannot be longer than 72 bytes"`, even for an 8-character
password. Root cause, confirmed by direct reproduction: `passlib` 1.7.4
(the library wrapping bcrypt) runs an internal self-test using a hardcoded
probe password, and that internal probe itself failed against bcrypt
5.x's stricter internal validation — nothing to do with the actual user's
password length at all. Fixed by pinning `bcrypt==4.1.3` in
`requirements.txt`, confirmed working by directly testing password
hashing before and after the version change. This is a real example of
a dependency version bump silently breaking a completely unrelated-seeming
feature.

## Rate limiting on auth endpoints

**File:** `app/core/rate_limiter.py` — a simple in-memory, per-IP,
fixed-window limiter (5 attempts per 60 seconds by default), applied to
`/auth/register` and `/auth/login`:

```python
class InMemoryRateLimiter:
    """
    Only effective within a single process - each worker has its
    own counters, so this does not enforce a global limit behind
    multiple Uvicorn/Gunicorn workers.
    """
```
That docstring is an honest, deliberate disclosure of a real limitation —
worth reading directly, it's the file's own author noting the tradeoff.

## How it works — a real walkthrough

1. User registers: `POST /auth/register` with email + password (8-72
   bytes, validated by `app/auth/schemas.py`).
2. Password is hashed with bcrypt, user row created in Postgres.
3. `POST /auth/login` verifies the password against the stored hash,
   returns a JWT valid for 30 minutes.
4. Every subsequent request (e.g. `POST /upload`) includes
   `Authorization: Bearer <token>`. `app/auth/dependencies.py`'s
   `get_current_user` decodes the token, looks up the user in Postgres,
   and injects it into the request handler.
5. `POST /chat` and `GET /documents` both pass `current_user.id` down to
   the retrieval layer, which filters ChromaDB and Postgres queries to
   only that user's documents (Sprint 6/7's `document_ids` filter, Sprint
   10's `get_user_document_ids`).

## Positive scenarios

- **Verified directly, live, during this project:** a second registered
  user attempting to `GET`/`DELETE` a document belonging to the first user
  correctly received `403` on every attempt — real cross-user isolation,
  not just intended behavior.
- Session restoration works correctly: a stored token from a deleted or
  since-wiped user correctly triggers a clean re-login flow rather than a
  confusing error (verified in the frontend, Sprint 13).

## Negative scenarios / limitations

- **The bcrypt version bug (above)** — a real, non-obvious dependency
  trap; anyone bumping `bcrypt` on this exact stack should know to test
  auth immediately after.
- **No refresh tokens** — a JWT expires in 30 minutes with no way to
  extend a session without a full re-login. A real UX limitation for any
  session longer than half an hour.
- **The rate limiter is per-process, not global** (its own author's
  documented caveat, above) — behind multiple worker processes or
  horizontal scaling, the *effective* rate limit is `5 × number of
  processes`, not a true global 5.
- **No email verification, no password reset, no "forgot password" flow**
  — confirmed by checking the full `app/auth/router.py` route list; these
  simply don't exist. A real, known gap for anything beyond a demo/
  portfolio context.
