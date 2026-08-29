# Sprint 11 — Production Engineering: Docker, CI/CD, Automated Tests

## The example at this step

Everything built so far worked on one specific laptop, run manually with
`uvicorn --reload`. This sprint makes sure that the exact flow — Sarah
uploading `Employee_Leave_Policy.pdf` and asking her sick-leave question —
behaves identically wherever the app runs, and that a broken change can't
reach `master` without a test catching it first.

## What we built

**File:** `Dockerfile` — a multi-stage build:
```dockerfile
FROM python:3.11-slim AS builder
RUN python -m venv /opt/venv
RUN pip install -r requirements.txt

FROM python:3.11-slim
RUN apt-get install -y --no-install-recommends libgomp1
COPY --from=builder /opt/venv /opt/venv
USER appuser
HEALTHCHECK ... CMD python -c "...urlopen('http://localhost:8000/health')"
CMD ["./entrypoint.sh"]
```

**File:** `docker-compose.yml` — runs the app + Postgres (and later,
ChromaDB and the worker) locally, matching production.

**File:** `.github/workflows/ci.yml` — runs the test suite on every push,
against a real Postgres service container.

## Classes & tools used, and why

| Tool | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| **Multi-stage Dockerfile** | Builds Python packages in one stage (`builder`, with a compiler available), then copies only the finished virtual environment into a clean final image | Keeps the shipped image smaller and avoids leaving a C compiler and build tools sitting in the container that actually runs in production | A single-stage build works, but ships every build-time dependency into the running container permanently, for no runtime benefit |
| `libgomp1` (explicitly installed) | Provides OpenMP, which PyTorch's CPU operations need at runtime | Without it, the exact code path that embeds Sarah's sick-leave chunk (Sprint 5, PyTorch-based) crashes the moment it actually runs — not at build time | Debian's `-slim` base images intentionally leave this out to stay small; it has to be added back explicitly for any PyTorch-based app |
| **Docker Compose** (local) | Runs Postgres, the web app, and (later) ChromaDB and the worker as connected containers on a laptop | Local testing then behaves the way production behaves — a concurrency issue between the web app and the worker (see Sprint 12) becomes visible on a laptop instead of only in production | Running the app directly on the host machine with `uvicorn --reload` hides exactly this class of multi-service bug until it's live |
| **GitHub Actions** (`.github/workflows/ci.yml`) | Runs the automated test suite against real `postgres:16-alpine` and `chromadb/chroma:1.5.9` containers, once per commit in a push | Catches a broken change (e.g. a function signature that no longer matches its caller) before it merges, using real services rather than mocks | Testing only locally, manually, before pushing relies entirely on remembering to do it every time — CI runs it automatically, every time, without being asked |
| `pytest-asyncio` (`asyncio_mode = "auto"`) | Lets `async def test_...()` functions actually execute under pytest | Without this plugin, pytest silently skips async test functions instead of failing loudly — meaning some tests were never actually running at all | — |

## How it works — Sarah's flow, containerized and tested

1. A developer pushes a commit that touches `app/services/chunker.py`.
2. A `discover-commits` job lists every commit included in that push.
3. `test` runs as a matrix over those commits — for each one, GitHub
   Actions checks it out individually, spins up a fresh runner plus real
   Postgres and ChromaDB containers, installs dependencies, runs
   `alembic upgrade head`, then runs `pytest`.
4. If a test exercising the upload → chunk → embed path fails on *any*
   commit in the push — not just the last one — that commit is flagged
   before it can be merged or deployed, before it could ever affect a
   real user like Sarah.
5. Locally, `docker compose up` runs the same containers CI and production
   use, so `Employee_Leave_Policy.pdf` can be uploaded and chatted with
   through the exact same code path that will run once deployed.

## A real gap in CI, found by a real failure

For a long stretch after Sprint 12 moved ChromaDB onto its own server,
`ci.yml` still only ran a Postgres service — nobody had gone back and
added a matching Chroma service when that architecture changed. Every
test that uploads or processes a document (anything touching
`VectorStoreService`) had nothing to connect to, and failed with
`ValueError: Could not connect to a Chroma server. Are you sure it is
running?`. This didn't show up locally, because a local `docker compose
up` always has a real Chroma container already running — the gap only
existed in CI's clean, from-scratch environment.

**The fix:** add a `chroma:1.5.9` service to `ci.yml`, using the exact
same `/dev/tcp` bash healthcheck `docker-compose.yml` already uses (no
`curl`/`wget`/`python` in that image — see Sprint 12), verified directly
against a real running container before committing.

**Testing every commit in a push, and a bug in that fix itself:** the
`discover-commits` job (above) needed the list of commits in a push,
pulled from `github.event.commits`. The first version wrote that
directly into the shell script: `echo '${{ toJson(github.event.commits)
}}' | ...`. A commit message containing an apostrophe (`"doesn't"`, in
one of this project's own commit messages) closed that single-quoted
string early, and the literal `(` from a normal `fix(ci): ...`-style
message right after it then ran as raw, invalid shell — a real syntax
error on the very next push after the feature was added. This is also
GitHub's own documented script-injection anti-pattern: untrusted text
(commit messages, author names) must be passed through `env:`, never
interpolated directly into `run:`. Fixed by passing it as an
`COMMITS_JSON` environment variable and reading `"$COMMITS_JSON"`
instead — verified locally against a message containing both an
apostrophe and parentheses before pushing again.

## Why `CMD`, not `ENTRYPOINT`

Sprint 12 later needed the same Docker image to run as two different
services — a web app and a worker — with two different startup commands.
Docker's `ENTRYPOINT` and `CMD` combine in a specific way (`CMD` becomes
*arguments to* `ENTRYPOINT`, not a replacement for it), and it wasn't
clearly documented whether Render's deployment platform fully replaces
`ENTRYPOINT` or just supplies new `CMD` arguments to it. The Dockerfile
uses `CMD` only, with no `ENTRYPOINT` — `CMD` is unambiguously,
fully replaceable, which removed the ambiguity entirely rather than
relying on an assumption.

## A transparent choice about test coverage

Eight test files are explicitly excluded from CI, each with a documented
reason in `.github/workflows/ci.yml`'s own comments — for example,
`test_gemini.py` needs a real API key not available in CI, and
`test_retrieval.py`'s test wasn't updated after `RetrievalService`'s
constructor changed in Sprint 10. A CI pipeline that's green because
failing tests were quietly deleted is worse than no CI at all — every
exclusion here is named and explained rather than hidden. See
[14-bugs-and-lessons-learned.md](14-bugs-and-lessons-learned.md) for the
full list.
