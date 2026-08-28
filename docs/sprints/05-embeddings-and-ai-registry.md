# Sprint 5 — Embedding Generation & AI Model Registry

## Objective

Computers can't compare "meaning" directly. To find "which chunks are
relevant to this question" without exact keyword matching, we need to
convert text into a numerical representation that captures *semantic*
meaning — where similar meanings produce similar numbers.

## What we built

**File:** `app/services/embedding.py`

```python
class EmbeddingService:
    def __init__(self):
        self.model = AIServiceRegistry.get_embedding_model()

    def generate(self, chunks: list[DocumentChunk]) -> list[DocumentEmbedding]:
        embeddings = []
        for chunk in chunks:
            vector = self.model.encode(chunk.content, convert_to_numpy=True)
            embeddings.append(DocumentEmbedding(
                chunk_id=chunk.chunk_id,
                embedding=vector.tolist(),   # a list of 384 floats
                ...
            ))
        return embeddings
```

**File:** `app/core/ai_registry.py` — the singleton pattern that loads the
model once and reuses it everywhere.

## Why `all-MiniLM-L6-v2` specifically

A real, deliberate tradeoff: this is one of the *smallest* widely-used
sentence-transformer models (~90MB), producing 384-dimension vectors (many
larger models produce 768 or 1024 dimensions). It's not the most accurate
embedding model available, but it's fast, lightweight, and runs on CPU with
no GPU required — a real constraint for a project meant to run on modest
infrastructure (this constraint became directly relevant later: see the
memory-ceiling problems in Sprint 12).

## The Singleton pattern — why loading a model once matters

Real problem this solves:

```
Bad:                          Good:
Request 1 → Load Model        Startup → Load Model Once
Request 2 → Load Model                → Reuse Everywhere
Request 3 → Load Model
```

Loading `all-MiniLM-L6-v2` from disk into memory is a real, measurable cost
(confirmed during this project: loading takes noticeable time, visible in
logs as `Loading embedding model: all-MiniLM-L6-v2`). Doing this on *every
request* would make every single API call slow. `AIServiceRegistry` uses a
Python classmethod with a class-level cache:

```python
class AIServiceRegistry:
    _embedding_model = None

    @classmethod
    def get_embedding_model(cls):
        if cls._embedding_model is None:
            from sentence_transformers import SentenceTransformer  # deferred
            cls._embedding_model = SentenceTransformer(settings.embedding_model)
        return cls._embedding_model
```
The model loads exactly once per process, on first use, and every
subsequent call reuses the same in-memory model.

## A real architectural lesson learned mid-project (not initially built this way)

The import of `sentence_transformers` (and therefore `torch`) was
**originally at the top of `ai_registry.py`**, not deferred inside the
method. This meant the moment `app.main` was imported — at process boot,
before the server even started listening for requests — the entire PyTorch
stack loaded, whether or not anyone had made a request needing embeddings
yet. This was fixed later (Sprint 12) once it became a real production
blocker: the deferred `from sentence_transformers import SentenceTransformer`
*inside* the method body is the fix, confirmed by checking `sys.modules`
before and after importing `app.main` — with the fix, zero heavy ML modules
load at boot.

## How it works — a real walkthrough

Given chunk `"Employees are entitled to 20 days of annual leave"`:

1. `self.model.encode(chunk.content, convert_to_numpy=True)` runs the text
   through the neural network.
2. Output: a 384-number vector, e.g. `[-0.0869, -0.0369, -0.0424, ...]`
   (these are real values observed during this project's testing — see
   `docs/sprints/14-bugs-and-lessons-learned.md` for the exact verification
   command used to inspect a real generated embedding).
3. Two chunks about similar topics ("leave policy," "vacation days")
   produce vectors that are numerically *close* to each other in this
   384-dimensional space; unrelated chunks produce distant vectors. This
   "closeness" is exactly what ChromaDB (Sprint 6) searches by.

## Positive scenarios

- Small, fast model means embedding generation for a short document
  (single chunk) completes in well under a second once the model is warm.
- The singleton pattern was verified to actually work — `test_ai_registry.py`
  confirms calling `get_embedding_model()` twice returns the *same* object,
  not two separately-loaded models.

## Negative scenarios / limitations

- **Cold start cost is real and user-visible.** The *first* embedding
  request after a process starts pays the full model-load cost — observed
  directly in this project's logs taking noticeably longer than subsequent
  calls. On a resource-constrained host (see Sprint 12), this cold start
  competed with other memory needs and contributed to real crashes.
- **384 dimensions is genuinely lower fidelity** than larger embedding
  models — for very nuanced or domain-specific text (e.g., legal or medical
  documents with subtle distinctions), this model may not distinguish
  concepts as precisely as a larger model would. This is a real accuracy
  tradeoff made for the sake of running on constrained infrastructure, not
  a limitation nobody noticed.
- No mechanism exists to swap embedding models after documents have already
  been embedded — changing `EMBEDDING_MODEL` in config would produce
  vectors from a different vector space than already-stored ones, silently
  breaking retrieval for old documents (a real risk if this setting were
  ever changed on a live system with existing data).
