# Sprint 9 — The Complete RAG Pipeline: Hybrid Search, Reranking, Conversation Memory, Hallucination Guard

## Objective

This was the largest single sprint: turn "retrieve some chunks, ask an LLM"
into a genuinely production-quality RAG pipeline — combining two different
search strategies, re-scoring results for quality, remembering conversation
context across messages, and actively checking the LLM's own answer for
accuracy before returning it to the user.

## 1. Hybrid Search — combining vector + keyword search

**File:** `app/services/hybrid_search.py`

Real problem this solves: pure vector (semantic) search sometimes misses
*exact* matches — e.g. if a user searches for a specific product code
"SKU-4471" or an exact proper name, semantic similarity might rank a
topically-related-but-wrong chunk higher than the chunk that literally
contains the exact string. **BM25** (`rank-bm25` library, `app/services/bm25_search.py`)
is a classic keyword-search algorithm that's excellent at exact term
matching but bad at paraphrases ("leave policy" vs "vacation days" — BM25
sees these as unrelated word sets).

```python
def search(self, ...):
    vector_results = self.vector_store.search(...)
    bm25_results = self.bm25_service.search(...)
    # combine both, weighted:
    # vector_weight=0.6, bm25_weight=0.4 (app/core/config.py)
```

Scores from both are normalized to 0-1 (see the *real bug* documented
below) and combined with configurable weights — vector search gets more
trust (0.6) than keyword search (0.4) by default, but both contribute.

### A real bug found and fixed in this exact code (distance normalization)

The original normalization formula was:
```python
return max(0, 1 - distance)   # WRONG for distance > 1
```
ChromaDB's L2 distance is **unbounded** (can exceed 1.0), so for any
distance greater than 1, this formula produces a *negative* similarity
score — nonsensical. Found and fixed to:
```python
return 1.0 / (1.0 + distance)   # always produces a valid 0-1 range
```
This exact formula reappears later, deliberately reused (not
reinvented) by the frontend for displaying relevance percentages —
documented in Sprint 13.

## 2. Reranking — a second, more precise scoring pass

**File:** `app/services/reranker.py`, model:
`cross-encoder/ms-marco-MiniLM-L-6-v2`

```python
class Reranker:
    def __init__(self):
        from sentence_transformers import CrossEncoder  # deferred, see bugs doc
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank(self, query, documents):
        pairs = [[query, doc.content] for doc in documents]
        scores = self.model.predict(pairs)
        for doc, score in zip(documents, scores):
            doc.rerank_score = 1 / (1 + math.exp(-float(score)))  # sigmoid
        return sorted(documents, key=lambda x: x.rerank_score, reverse=True)[:3]
```

**Why rerank at all, if hybrid search already ranked results?** A real,
important distinction: the embedding model (Sprint 5) scores a query
against *each chunk independently*, fast, at scale (good for narrowing
thousands of chunks down to ~10). A **cross-encoder** looks at the query
and a candidate chunk *together*, jointly, which is far more accurate at
judging true relevance — but too slow to run against every chunk in a
large collection. The two-stage pattern (fast broad retrieval → precise
reranking of just the top candidates) is a standard, real information-
retrieval technique, not a redundant step.

**A real, un-fixed inefficiency found in this exact code:** `Reranker()`
is instantiated fresh on *every single* `/chat` request (inside
`RAGChatService.__init__`), reloading the cross-encoder model from disk
every time — it does **not** go through the `AIServiceRegistry` singleton
pattern that the embedding model (Sprint 5) correctly uses. This was
identified during this project as a real, confirmed performance
characteristic (every chat message pays a model-load cost) but was left
as a known limitation rather than fixed, since fixing it was out of scope
for the sprint that found it.

## 3. Conversation Memory — multi-turn context

**File:** `app/services/conversation_store/memory.py`,
`app/services/conversation.py`

```python
class InMemoryConversationStore(ConversationStore):
    def __init__(self):
        self.store = {}   # {conversation_id: [messages]}
```

A **real, deliberate architectural characteristic, confirmed by reading
every usage of this class:** conversation history lives entirely in a
Python dictionary in process memory. There is **no database table**, no
file, nothing persisted. This means:
- A server restart (deploy, crash, scale-to-zero) wipes **all**
  conversation history for **every** user, instantly, with no warning.
- There is no `GET /conversations` endpoint to list past conversations —
  confirmed by grepping the entire API surface — because there's no way to
  look up "which conversation IDs exist for this user," only "given a
  conversation ID, what messages does it have."

This directly shaped a real downstream decision: when building the
frontend (Sprint 13), a "Chat History" sidebar feature was deliberately
**not built**, specifically because there's no backend capability to
support it honestly.

## 4. Hallucination Guard — verifying the LLM's own answer

**File:** `app/services/hallucination_guard_service.py`

This is a genuine two-pass mechanism, not just a prompt instruction. The
*real* flow, confirmed by reading `app/services/rag_chat.py` line by line:

```
1. LLM generates an initial answer from the retrieved context.
2. A SECOND LLM call asks: "is this answer fully supported by the context?"
   returning JSON: {"grounded": true/false, "confidence": 0-1, "unsupported_claims": []}
3. IF NOT grounded:
   → logs "Hallucination detected. Regenerating response"
   → re-generates the answer using a STRICTER prompt that explicitly
     instructs: 'If information is missing say: "I don't have enough
     information."'
```

**Real, important cost consequence:** when the guard triggers, a single
user question results in **three separate LLM API calls** (initial
generation + validation + regeneration), not one. This is a genuine
latency and cost multiplier under this exact, confirmed code path.

**Verified live, during this project:** asking a follow-up question the
uploaded document didn't cover ("Can you give an example application?"
against a document that only *defined* AI, with no examples) correctly
triggered the guard and returned "I don't have enough information from
the provided documents" — this was directly observed in production
testing, not assumed.

## 5. Source Citations & Context Window Management

**Files:** `app/services/source_builder.py`, `app/services/context_window_manager.py`

`SourceBuilder` converts raw retrieval results into `SourceReference`
objects (`document_id`, `chunk_id`, `filename`, `content`, `score`,
`rerank_score`) that get returned to the caller alongside the answer —
this is what powers the frontend's "Based on N sources" UI (Sprint 13).

`ContextWindowManager` deduplicates and compresses retrieved chunks before
they're stuffed into the LLM prompt, staying under a token budget
(`max_context_tokens=4000`) — a real, practical constraint: LLMs have
finite context windows, and naively concatenating every retrieved chunk
could exceed it or waste tokens on redundant overlapping content.

## Positive scenarios

- Hybrid search genuinely improves result quality over either method
  alone for realistic queries — verified conceptually and via the real
  test documents used throughout this project.
- The hallucination guard's regeneration path was directly observed
  working correctly in production testing (see above) — not a
  theoretical feature, a confirmed working safety mechanism.
- Multi-turn conversation correctly threads context between messages
  within a single server process lifetime — verified live with real
  follow-up questions during this project's frontend testing.

## Negative scenarios / limitations (honest, not hidden)

- **Conversation history is entirely non-persistent** (above) — a real,
  significant limitation for anything beyond a single browser session.
- **The reranker reloads its model on every request** — a real,
  un-optimized performance cost, left as a known issue.
- **The hallucination guard triples LLM cost/latency when triggered** —
  no caching or cheaper heuristic check exists before committing to the
  full second LLM call.
- **No streaming** — the user waits for the *entire* multi-call pipeline
  (retrieval → rerank → generate → validate → possibly regenerate) to
  finish before seeing anything, which can take several real seconds,
  confirmed during live testing (often 5-15+ seconds end to end,
  especially on a cold-started process still loading models).
