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

## Found after initial deployment — a real performance bug and a missing feature

These two were found later, while using the deployed app for real (asking
Sarah's exact question), not during the original build:

| # | Issue | Root cause | Fix | Detail |
|---|---|---|---|---|
| 21 | Every `/chat` response took several seconds longer than it needed to, even on a warm process — a question that should answer in ~3 seconds was taking ~14 | `Reranker()` (the cross-encoder used for reranking, Sprint 9) was constructed fresh inside `RAGChatService.__init__` on every single request, reloading its model from disk each time — unlike the embedding model, it never went through `AIServiceRegistry`'s singleton | Added `AIServiceRegistry.get_reranker()`, following the exact same pattern already used for the embedding model; `RAGChatService` now calls it instead of `Reranker()` directly. Measured directly: a warm request dropped from ~14s to ~2.9s | [Sprint 5](05-embeddings-and-ai-registry.md), [Sprint 9](09-rag-pipeline-and-hybrid-search.md) |
| 22 | Sarah had no way to tell, from the chat UI, whether an answer came from a strong match in her document or a weak, borderline one | `SearchEvaluator` (Sprint 9) had computed an `Excellent`/`Good`/`Weak` quality label and returned it in every `/chat` response from the start — but no frontend component ever read `search_evaluation` | Added `AnswerQualityBadge`, wired to `response.search_evaluation.quality` and `.best_score`; verified live showing "Excellent match · 78%" on Sarah's sick-leave question | [Sprint 9](09-rag-pipeline-and-hybrid-search.md), [Sprint 13](13-frontend-nextjs.md) |

Also worth noting directly: the actual generation is done by **Ollama**
(`llama3.1`, running locally), not Gemini — set by `LLM_PROVIDER` in
`.env`. Local CPU inference is inherently slower than a cloud API call,
and the hallucination guard (Sprint 9) doubles that cost by making a
second LLM call to validate every answer. The reranker fix above removes
one real, avoidable delay; switching `LLM_PROVIDER=gemini` would remove
the larger, structural one, at the cost of a per-call API fee instead of
local compute time.

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
