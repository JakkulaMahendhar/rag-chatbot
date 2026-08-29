# Bugs & Lessons Learned — A Consolidated, Honest Record

Every entry here is a **real, reproduced** bug found while building the
exact pipeline documented in this folder — the one that takes Sarah's
`Employee_Leave_Policy.pdf` from upload to a correct chat answer. Each was
diagnosed with evidence (logs, tracebacks, direct testing), not guessed
at. This file is a quick index; see the linked sprint file for the full
diagnosis story, including why the eventual fix works better than the
approach it replaced.

## Backend bugs

| # | Bug | Root cause | Fix | Detail |
|---|---|---|---|---|
| 1 | `chromadb.errors.InternalError: Error finding id` on `/chat` and `/search` | `VectorStoreService` opened a fresh embedded ChromaDB client per call, bypassing an unused singleton; two separate processes (web + worker) both touched the same embedded storage concurrently — not designed for that | Run ChromaDB as its own server, both processes connect via `HttpClient` over HTTP | [Sprint 12](12-deployment-and-worker-queue.md) |
| 2 | App OOM-killed on Render (`Out of memory (used over 512Mi)`) | PyTorch + embedding model loaded eagerly at process boot | Deferred `AIServiceRegistry` calls | [Sprint 12](12-deployment-and-worker-queue.md) |
| 3 | Same OOM problem persisted after fix #2 | The eager *import* (not just the call) of `sentence_transformers`/`torch` was still at module top-level | Moved imports inside method bodies | [Sprint 12](12-deployment-and-worker-queue.md) |
| 4 | Importing `langchain_text_splitters` alone pulls in ~3,900 modules including `torch` | The package's own `__init__.py` re-exports tokenizer-based splitters regardless of which class you use | Deferred import inside `ChunkingService.__init__` | [Sprint 4](04-chunking-and-storage.md), [Sprint 12](12-deployment-and-worker-queue.md) |
| 5 | Every registration/login failed: `"password cannot be longer than 72 bytes"` for any password length | `bcrypt==5.0.0`'s stricter validation broke `passlib==1.7.4`'s own internal self-test probe — unrelated to actual password length | Pinned `bcrypt==4.1.3` | [Sprint 10](10-authentication-and-multiuser.md) |
| 6 | Worker container crashed on startup: `"column already exists"` | Both web and worker entrypoints ran `alembic upgrade head` concurrently; a genuine race under Postgres's DDL locking | Migrations run only from the web service's entrypoint | [Sprint 12](12-deployment-and-worker-queue.md) |
| 7 | Chroma server container's healthcheck would have hung forever | The official `chromadb/chroma` image ships neither `curl`, `wget`, nor `python` | Healthcheck using bash's `/dev/tcp`, invoked via explicit `CMD ["bash", "-c", ...]` (not `CMD-SHELL`, which runs via `dash`, which doesn't support `/dev/tcp`) | [Sprint 12](12-deployment-and-worker-queue.md) |
| 8 | Local ChromaDB distance-to-similarity conversion produced negative scores | Original formula `1 - distance` breaks for any distance > 1, which is valid for unbounded L2 distance | Changed to `1 / (1 + distance)` | [Sprint 9](09-rag-pipeline-and-hybrid-search.md) |
| 9 | An entire `.env` file was accidentally overwritten with placeholder values mid-session | `cp .env.example .env` run without backing up first | Values reconstructed manually (real Postgres role checked directly, fresh JWT secret generated); real data itself was untouched, only the connection string was lost | (session-level incident, not a code bug — recorded here as a process lesson) |

## Frontend bugs

| # | Bug | Root cause | Fix | Detail |
|---|---|---|---|---|
| 10 | Sources/search results showed a UUID filename instead of the real document name | Chunk metadata stores the on-disk storage filename (Sprint 2), never the original upload name | Cross-referenced `document_id` against the real documents list from Postgres | [Sprint 13](13-frontend-nextjs.md) |
| 11 | Search/chat relevance would have displayed as a nonsensical or backwards "% match" | `score` is a raw, unbounded Chroma L2 distance, not a 0-100% similarity | Reused the backend's own `1/(1+distance)` formula rather than inventing a new one | [Sprint 13](13-frontend-nextjs.md) |
| 12 | `asChild` prop usage caused TypeScript errors on every dropdown/dialog trigger | The generated shadcn/ui components are built on Base UI, not Radix — different composition API (`render` prop) | Rewrote every trigger-wrapping component to use `render` | [Sprint 13](13-frontend-nextjs.md) |
| 13 | Runtime crash: `"Base UI: MenuGroupContext is missing"` | `DropdownMenuLabel` used without a required `DropdownMenuGroup` wrapper | Wrapped it correctly | [Sprint 13](13-frontend-nextjs.md) |
| 14 | Mobile navigation drawer didn't reliably close after tapping a nav link | The Link's `onClick` handler raced against Next's own client-side navigation | Closed the drawer via a `usePathname()`-driven effect instead | [Sprint 13](13-frontend-nextjs.md) |
| 15 | Static-export build baked in `localhost:8000` instead of the production API URL | `.env.local` takes precedence over `.env.production` in Next.js's env-loading order | Confirmed this only affects local rebuilds (`.env.local` is gitignored, absent on a clean deploy checkout) by testing without it present | [Sprint 13](13-frontend-nextjs.md) |
| 16 | Delete button appeared visually disabled despite being fully active | Used the `ghost` button variant with no explicit color, inheriting a low-contrast muted tone | Switched to the `destructive` variant with an explicit solid background | [Sprint 13](13-frontend-nextjs.md) |

## Testing/CI bugs

| # | Bug | Root cause | Fix | Detail |
|---|---|---|---|---|
| 17 | Several `async def test_...()` functions never actually ran | No `pytest-asyncio` plugin installed — pytest silently no-ops un-awaitable async tests instead of failing | Installed `pytest-asyncio`, set `asyncio_mode = "auto"` | [Sprint 11](11-production-engineering-docker-ci.md) |
| 18 | A test using the same TestClient fixture as other tests failed with a cross-event-loop error | A session-scoped `TestClient` fixture and pytest-asyncio's per-test event loop both touched one global async SQLAlchemy engine | Diagnosed as a genuine architecture limitation, documented and excluded rather than papered over | [Sprint 11](11-production-engineering-docker-ci.md) |
| 19 | `test_retrieval.py` fails with `TypeError` | `RetrievalService`'s constructor signature changed (Sprint 10, to accept a DB session) without updating this test | Documented, intentionally left for separate follow-up work | [Sprint 7](07-semantic-retrieval.md), [Sprint 11](11-production-engineering-docker-ci.md) |
| 20 | CI initially failed on `test_llm.py` | The test calls the real configured LLM provider (`ollama` by default) — GitHub's CI runner has no Ollama daemon, unlike the machine this was first validated on | Excluded with a documented reason | [Sprint 8](08-llm-integration.md), [Sprint 11](11-production-engineering-docker-ci.md) |

## Found after initial deployment — real bugs, a missing feature, and a near-miss

Found later, while using the deployed app for real (asking Sarah's exact
question), not during the original build:

| # | Issue | Root cause | Fix | Detail |
|---|---|---|---|---|
| 21 | Every `/chat` response took several seconds longer than it needed to, even on a warm process — a question that should answer in ~3 seconds was taking ~14 | `Reranker()` (the cross-encoder used for reranking, Sprint 9) was constructed fresh inside `RAGChatService.__init__` on every single request, reloading its model from disk each time — unlike the embedding model, it never went through `AIServiceRegistry`'s singleton | Added `AIServiceRegistry.get_reranker()`, following the exact same pattern already used for the embedding model; `RAGChatService` now calls it instead of `Reranker()` directly. Measured directly: a warm request dropped from ~14s to ~2.9s | [Sprint 5](05-embeddings-and-ai-registry.md), [Sprint 9](09-rag-pipeline-and-hybrid-search.md) |
| 22 | Sarah had no way to tell, from the chat UI, whether an answer came from a strong match in her document or a weak, borderline one | `SearchEvaluator` (Sprint 9) had computed an `Excellent`/`Good`/`Weak` quality label and returned it in every `/chat` response from the start — but no frontend component ever read `search_evaluation` | Added `AnswerQualityBadge`, wired to `response.search_evaluation.quality` and `.best_score`; verified live showing "Excellent match · 78%" on Sarah's sick-leave question | [Sprint 9](09-rag-pipeline-and-hybrid-search.md), [Sprint 13](13-frontend-nextjs.md) |
| 23 | The very first real Gemini call after adding an API key failed: `google.api_core.exceptions.NotFound: 404 This model models/gemini-2.5-flash is no longer available to new users` | Google deprecated `gemini-2.5-flash` for this API key between when the project started and when Gemini was first actually exercised end-to-end — the config default had never been re-verified against a real call | Google's own error named the replacement directly; updated `GEMINI_MODEL` to `gemini-3.6-flash` in `.env`, `.env.example`, and `Settings.gemini_model`'s default. Re-verified live: same question, `HTTP 200`, correct answer | [Sprint 8](08-llm-integration.md) |
| 24 | A real Gemini API key ended up typed into `.env.example` (git-tracked) instead of `.env` (git-ignored) while testing the provider toggle | `.env.example` and `.env` look nearly identical and sit next to each other; the key was added to the wrong one by hand | Caught by reviewing `git diff` before staging — moved the key to `.env`, reset `.env.example` back to blank, confirmed with a clean `git diff .env.example` before ever running `git add`. Never reached a commit, so no history rewrite was needed | (process lesson, not a code bug — the same category as bug #9) |
| 25 | Every real Gemini answer logged `{'grounded': False, 'confidence': 0, 'unsupported_claims': ['Unable to validate response']}` — even answers that were correct — and every Gemini message paid for a needless extra "regenerate" call | `HallucinationGuardService._parse_response()` called `json.loads()` directly on Gemini's response, but Gemini wraps JSON in a ` ```json ` markdown fence even when told not to; the parse always failed and fell through to a hardcoded "ungrounded" default | Strip a leading/trailing ` ``` ` fence before parsing, mirroring the fix `QueryExpander` already had for the same problem in a different file. Verified live: the same question that always logged `grounded: False` now correctly logs `grounded: True, confidence: 1` | [Sprint 9](09-rag-pipeline-and-hybrid-search.md) |
| 26 | A Gemini chat request that hit a quota limit took ~145 seconds and then returned a bare, unhandled `500 Internal Server Error` | The account's Gemini API key is on the free tier (20 requests/day for `gemini-3.6-flash`); once exceeded, Google's client library retries with backoff internally before finally raising `google.api_core.exceptions.ResourceExhausted`, which `POST /chat` didn't catch | Added a narrow `except GoogleAPIError` around the chat call in `app/api/chat.py`, returning a `503` with Google's own message. Doesn't fix the quota itself (that needs billing or waiting for the daily reset) — but turns a silent, minutes-long hang into an immediate, readable error | [Sprint 8](08-llm-integration.md) |
| 27 | GitHub Actions CI failed continuously with `ValueError: Could not connect to a Chroma server. Are you sure it is running?` on every document-related test | Sprint 12 moved ChromaDB onto its own server, but `ci.yml` was never updated to run one — it only ever had a Postgres service. Invisible locally, since a local `docker compose up` always has a real Chroma container already running | Added a `chroma:1.5.9` service to `ci.yml`, mirroring `docker-compose.yml`'s exact `/dev/tcp` healthcheck, verified against a real running container before committing | [Sprint 11](11-production-engineering-docker-ci.md) |
| 28 | The very next push after fix #27 broke CI again, this time with a bare shell `syntax error near unexpected token '('` inside a brand-new `discover-commits` job | That job (added the same day, to test every commit in a push instead of just the pushed tip) wrote `${{ toJson(github.event.commits) }}` directly into a single-quoted shell string; an apostrophe in a commit message (`"doesn't"`) closed the quote early, and the literal `(` from the next `fix(ci): ...`-style message ran as raw, invalid shell | Passed the commit JSON through `env: COMMITS_JSON: ...` instead of interpolating it into the script, and read `"$COMMITS_JSON"` — this is also GitHub's own documented fix for the underlying script-injection risk, not just the syntax error. Verified locally against a message containing both an apostrophe and parentheses | [Sprint 11](11-production-engineering-docker-ci.md) |
| 29 | Asked a broad question, the LLM's answer sometimes read like a raw context dump: *"Machine learning ... (Source 2, Chunk ID: 6-6, Content: 1.1 What Is Machine Learning?)"* instead of a written answer | `ContextFormatter` labels retrieved chunks with `SOURCE N / Chunk ID / Similarity Score` for the LLM's own reference, but `PromptBuilder`'s rules never told it not to repeat those labels verbatim — Ollama's `llama3.1` sometimes just copied them into its answer | Added an explicit rule to `PromptBuilder` and the hallucination guard's strict regeneration prompt: the labels are for reference only, never to be reproduced — real source attribution is already shown separately by the frontend. Verified against the same question afterward: clean prose, no leakage | [Sprint 9](09-rag-pipeline-and-hybrid-search.md) |
| 30 | Retrieval quality quietly degraded over time — weak match scores, and the hallucination guard genuinely triggering on questions that used to work fine | `docker-compose.yml`'s named volume was mounted at `/chroma/chroma`, but the `chromadb/chroma:1.5.9` image's own baked-in config hardcodes `persist_path: "/data"` — a completely different, unmounted path. Chroma had been writing every vector to the container's disposable filesystem layer the whole time; the volume mount was a no-op. Every container recreation silently lost all vector data, while Postgres (mounted correctly) kept everything — old documents stayed `status: "completed"` with no actual retrievable content left | `chroma run` refuses to combine its config-file argument with `--path`/`--host` (confirmed directly against the image), so the config file was dropped for explicit flags: `command: ["run", "--path", "/chroma/chroma", "--host", "0.0.0.0"]`. Verified with a real `--force-recreate` cycle, not just a restart (which would've looked fine even under the old broken setup) — a document's chunks survived. Any document uploaded before this fix needs to be re-uploaded; there's nothing left to recover | [Sprint 6](06-vector-database-chromadb.md) |

Also worth updating: with the frontend's AI Model toggle in place (Sprint
8/13), which provider answers a given question is no longer fixed for the
whole server — it's chosen per request, defaulting to Ollama. Ollama still
means local CPU inference, genuinely slower than a cloud call, and the
hallucination guard (Sprint 9) still makes a second LLM call to validate
every answer — the reranker fix above removes one real, avoidable delay
regardless of provider; the JSON-parsing fix (#25) removes another,
Gemini-specific one. Gemini itself is not necessarily faster in practice:
on the free tier, its own request quota (#26) is the binding constraint,
not raw model speed.

## The single biggest lesson from this project

**Every one of the bugs above that mattered most (1-9) was only findable by
actually running the real, multi-process, containerized system under real
conditions — not by reading the code, not by unit tests, not by assuming
"it built successfully" meant "it works."** The ChromaDB concurrency bug
specifically required reproducing on a *fresh install* to distinguish a
real architectural issue from accumulated test-session noise. This is the
concrete argument for why Sprint 11 (making local dev match production via
Docker) came before Sprint 12 (deployment) — without that parity, most of
these bugs would have been discovered for the first time in production,
with real users affected, instead of in controlled local testing first.

Bug #30 (the volume mount that was silently never used) makes the same
point in an even sharper way: it produced *no error at all* — no crash,
no failed healthcheck, nothing in the logs to grep for. `docker compose
up`/`down` ran cleanly every time. The only symptom was retrieval quality
degrading gradually, discovered only because answers that used to work
started coming back weak or "not grounded." A quick `restart` of the
container would have looked like proof the volume worked, since the same
container's disposable layer survives a restart — only testing a genuine
recreation (`--force-recreate`) exposed it. The lesson: for anything
claiming to persist data, "it didn't crash" is not evidence it's actually
persisting — only checking the data survives a real recreation is.
