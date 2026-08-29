# Sprint 7 — Semantic Retrieval

## The example at this step

Sarah types: *"How many sick leaves do I get per year?"* This step turns
that question into the actual set of chunks worth answering from — and
just as importantly, decides when there's *nothing* relevant to answer
from, so the system doesn't guess.

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

**File:** `app/core/config.py` — one typed, centralized settings object:

```python
class Settings(BaseSettings):
    top_k_vector: int = 10
    vector_distance_threshold: float = 0.75   # cosine distance cutoff
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
```

## Classes & libraries used, and why

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `RetrievalService.retrieve()` | Asks ChromaDB for the closest chunks to Sarah's question, then drops any that are too far away to be genuinely relevant | Separates "how do we search" from "what do we do with the result," so the rest of the RAG pipeline just calls one method | Calling `vector_store.search()` directly from every place that needs a chunk would spread the threshold-filtering logic across the codebase instead of keeping it in one place |
| `vector_distance_threshold` (0.75) | A hard cutoff — a chunk further than this distance from the question is excluded, even if it's the closest thing available | If Sarah asked about something the document simply doesn't cover (e.g. "what's the office parking policy?"), always returning the "top 5 closest" chunks anyway would hand the LLM the *least irrelevant* junk and risk a made-up answer | Returning a fixed top-K regardless of distance means there's no way to say "nothing here is actually relevant" — this threshold is exactly what lets the hallucination guard (Sprint 9) correctly answer "I don't have enough information" |
| `Settings` (Pydantic Settings) | One typed object holding every tunable value (`chunk_size`, `top_k_vector`, `vector_distance_threshold`, …), loaded from `.env` | The exact same code runs against a local Postgres and a Render-hosted Postgres purely by changing `.env` — and Pydantic validates every value's type at startup, so a bad `.env` value fails immediately with a clear error instead of misbehaving deep in some unrelated code path later | Hardcoded values scattered across files mean changing one tunable setting (like the weighting between vector and keyword search, Sprint 9) means hunting through multiple files instead of editing one class |

## How it works — retrieving for Sarah's question

1. Sarah's question is embedded into a query vector (Sprint 5).
2. `RetrievalService.retrieve()` asks ChromaDB for the top 10
   (`top_k_vector`) closest chunks across her documents.
3. Chunk `"14-1"` (the sick-leave sentence) comes back with a small
   distance, e.g. `0.3` — well within the `0.75` threshold, so it's kept.
4. A chunk from an unrelated part of the handbook (say, an office-hours
   paragraph) might come back with distance `0.9` — past the threshold,
   so it's dropped, even though it was technically one of the "top 10
   closest."
5. Only the chunks that pass the threshold move forward to hybrid search
   and reranking (Sprint 9).

This is the mechanism that makes the difference between *"the system found
something loosely related and guessed"* and *"the system found the actual
answer, or correctly said it doesn't have one."*
