# Sprint 5 — Embedding Generation & AI Model Registry

## The example at this step

Chunk `"14-1"` — the piece of `Employee_Leave_Policy.pdf` containing *"All
full-time employees are entitled to 12 paid sick leaves per calendar year,
accrued monthly at 1 leave per month"* — is still just text. A computer
can't compare "meaning" between two pieces of text directly. This step
turns that chunk into a list of numbers that captures what it *means*, so
it can later be compared to Sarah's question by meaning, not just exact
words.

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

**File:** `app/core/ai_registry.py` — loads the embedding model once and
reuses it for every chunk and every question, instead of reloading it
every time. It caches three things this way: the embedding model, the LLM
client, and (see Sprint 9) the reranker's cross-encoder model.

## Classes & libraries used, and why

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `all-MiniLM-L6-v2` (via `sentence-transformers`) | Converts a piece of text into a 384-number vector | Small (~90MB), fast, runs on CPU with no GPU needed — the whole app needs to run on a modest, low-memory server | Larger embedding models (e.g. 768- or 1024-dimension models) can be more precise but cost more memory and are slower per chunk; for a policy document like Sarah's, the smaller model is accurate enough while staying light |
| `AIServiceRegistry` (singleton) | Loads `all-MiniLM-L6-v2` into memory exactly once per process, and hands out the same loaded model to every caller | Loading a model from disk is a real, measurable cost; paying it once at first use instead of on every single request keeps every chunk and every question fast after the first one | Creating `SentenceTransformer(...)` fresh inside every function call would reload the model from disk on every single upload and every single chat message — far slower, and wasteful of memory |
| `.encode(text, convert_to_numpy=True)` | Runs the text through the neural network and returns the vector as a NumPy array | NumPy arrays convert cleanly to the plain Python list ChromaDB expects | — |

## How it works — embedding Sarah's sick-leave sentence

1. `EmbeddingService.generate()` is called on chunk `"14-1"`.
2. `self.model.encode(chunk.content, convert_to_numpy=True)` runs that
   text through the neural network.
3. The output is a 384-number vector, e.g. `[-0.0869, -0.0369, -0.0424, ...]`.
4. This vector doesn't mean anything to a human by itself — but a chunk
   about *"vacation days"* or *"annual leave"* would produce a vector that
   sits numerically *close* to this one in 384-dimensional space, while a
   chunk about, say, *"office parking"* would sit far away. That
   "closeness" is exactly what ChromaDB (Sprint 6) searches by later, and
   it's *why* semantic search can match Sarah's question even if she
   phrases it differently from the document's exact wording.

## Why the model is loaded once, not per request

```
Without the registry:                With the registry:
Upload 1 → load model                Startup → load model once
Chat msg 1 → load model                       → every upload/question
Chat msg 2 → load model                          reuses it
```

`AIServiceRegistry` keeps a class-level cache:

```python
class AIServiceRegistry:
    _embedding_model = None
    _reranker = None

    @classmethod
    def get_embedding_model(cls):
        if cls._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            cls._embedding_model = SentenceTransformer(settings.embedding_model)
        return cls._embedding_model

    @classmethod
    def get_reranker(cls):
        if cls._reranker is None:
            from app.services.reranker import Reranker
            cls._reranker = Reranker()
        return cls._reranker
```

The model loads exactly once per process, the first time anyone needs it —
whether that's embedding Sarah's uploaded chunk, or later embedding her
typed question — and every call after that reuses the same in-memory
model.

## A real bug this exact pattern fixed, found after going live

`get_reranker()` wasn't part of the registry when Sprint 9's reranker
(the cross-encoder that re-scores search results) was first built —
`RAGChatService` called `Reranker()` directly instead, which reloaded the
cross-encoder model from disk on **every single `/chat` request**. This
went unnoticed until Sarah's actual chat responses were timed: log
timestamps showed `Initializing RAGChatService` to `Reranker initialized`
consistently taking several extra seconds on every message, warm or not —
exactly the cost this file's own singleton pattern was built to avoid for
the embedding model. Adding `get_reranker()` above and pointing
`RAGChatService` at it fixed it: a warm chat request that took ~14 seconds
dropped to ~2.9 seconds. See
[09-rag-pipeline-and-hybrid-search.md](09-rag-pipeline-and-hybrid-search.md)
for where the reranker is actually used, and
[14-bugs-and-lessons-learned.md](14-bugs-and-lessons-learned.md) for the
full timing evidence.
