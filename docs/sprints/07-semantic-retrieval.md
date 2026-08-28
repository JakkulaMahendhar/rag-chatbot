# Sprint 7 — Semantic Retrieval

## Objective

Sprint 6 gave us the ability to store and query vectors. This sprint turns
that into an actual usable service: take a user's typed question, and
return the most relevant stored chunks — plus refactor the configuration
and retrieval logic into a clean, reusable service layer (Sprints 7.1/7.2 in
the original roadmap).

## What we built

**File:** `app/services/retrieval.py`

```python
class RetrievalService:
    def retrieve(self, query_embedding, top_k=5, document_ids=None):
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
        )
        # filters by vector_distance_threshold before returning
```

**File:** `app/core/config.py` — centralized, typed configuration via
Pydantic Settings (Sprint 7.2's "centralize application configuration"):

```python
class Settings(BaseSettings):
    top_k_vector: int = 10
    vector_distance_threshold: float = 0.75   # cosine distance cutoff
    ...
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
```

## Why a distance *threshold*, not just top-K

Real problem: if you always return the "top 5" results no matter what,
irrelevant results get returned when a document genuinely has *nothing*
relevant to a question (e.g., asking about "refund policy" against a
document about "office locations"). The top 5 closest vectors would still
be returned even though none of them are actually relevant — just the
*least irrelevant* of a bad set. `vector_distance_threshold` sets a hard
cutoff: results past this distance are excluded even if it means returning
fewer than `top_k` results, or zero. This exact mechanism is what allows
the later hallucination guard (Sprint 9) to correctly say "I don't have
enough information" instead of confidently answering from irrelevant
context.

## Why centralize configuration (Sprint 7.2)

Before this, settings were scattered as hardcoded values across files.
Centralizing into one `Settings` class, loaded from `.env`, gave three real
benefits, each later exercised concretely in this project:
1. **Environment-specific behavior without code changes** — the exact same
   code runs against `localhost` Postgres locally and a Render-hosted
   Postgres in production, purely by changing `.env` values.
2. **A single source of truth for tuning.** When hybrid search (Sprint 9)
   needed weighting between vector and keyword results, `vector_weight` /
   `bm25_weight` were added here, not scattered through the codebase.
3. **Validation for free** — Pydantic Settings validates types at startup
   (e.g., `chunk_size: int` — if `.env` has a non-numeric value, the app
   fails to start immediately with a clear error, rather than failing
   confusingly deep in some unrelated code path later).

## How it works — a real walkthrough

User asks: *"What is the leave policy?"*

1. The question is embedded into a query vector (Sprint 5).
2. `RetrievalService.retrieve()` asks ChromaDB for the top 10
   (`top_k_vector`) closest chunks.
3. Each result's distance is compared against `vector_distance_threshold`
   (0.75). A chunk about leave policy might have distance `0.3` (well
   within threshold, kept). A chunk about an unrelated topic might have
   distance `0.9` (excluded).
4. Only the chunks that pass the threshold move forward to the next stage
   (hybrid search combination, reranking — Sprint 9).

## Positive scenarios

- Correctly distinguishes relevant from irrelevant content when a document
  genuinely doesn't cover the asked topic — verified live: asking "Can you
  give an example application?" against a document that only defined AI
  (no examples) correctly triggered "I don't have enough information," not
  a fabricated answer, because retrieval + the hallucination guard (Sprint
  9) worked together correctly.

## Negative scenarios / limitations

- The threshold (`0.75`) is a single global value, not adaptive — a
  genuinely relevant but oddly-phrased chunk near the boundary might get
  excluded, or an irrelevant-but-topically-adjacent chunk might get
  included. Real embedding-based retrieval always has this fuzzy-boundary
  characteristic; there's no tuning-free solution.
- `RetrievalService`'s constructor signature changed during later
  development (to accept a database session for per-user filtering,
  Sprint 10) without the corresponding test being updated — a real,
  currently-existing broken test (`tests/test_retrieval.py`, confirmed
  failing with `TypeError`) that was found, diagnosed, and intentionally
  left unfixed as out-of-scope for the sprint that found it (see the CI
  documentation in Sprint 11 for how this was handled — excluded from the
  automated test run with the reason documented, not silently ignored).
