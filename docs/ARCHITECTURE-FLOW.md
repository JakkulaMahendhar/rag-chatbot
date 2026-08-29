# End-to-End Architecture: Upload → Answer

One concise view of the whole system — every concept implemented, in the
order data actually flows through it. Two flows: **ingesting a document**
and **answering a question**. Detailed per-sprint reasoning lives in
`docs/sprints/`; this is the map.

```
════════════════════════ 1. INGESTION FLOW (upload) ════════════════════════

 Browser                Web App (FastAPI)              Worker (background)
 ───────                ─────────────────              ────────────────────
 upload PDF ──POST /upload──▶ save file as UUID
                              create Document row              polls every 5s
                              status="pending"                 for status=pending
                              return 202 immediately ──▶            │
                                                                     ▼
                                                          ParserService
                                                          (PyMuPDF / python-docx)
                                                          binary → plain text
                                                                     │
                                                                     ▼
                                                          ChunkingService
                                                          (RecursiveCharacterTextSplitter
                                                           chunk_size=1000, overlap=200)
                                                                     │
                                                                     ▼
                                                          EmbeddingService
                                                          (all-MiniLM-L6-v2
                                                           → 384-dim vector per chunk)
                                                                     │
                                                    ┌────────────────┴────────────────┐
                                                    ▼                                  ▼
                                          ChromaDB Server                       BM25 Index
                                          (vector store, HTTP)                  (keyword index)
                                                    │                                  │
                                                    └────────────────┬────────────────┘
                                                                     ▼
                                                          status="completed"
                                                     (frontend polling picks this up)


════════════════════════ 2. QUERY FLOW (ask a question) ════════════════════

 Browser                          Web App (FastAPI) — RAGChatService
 ───────                          ───────────────────────────────────
 "How many sick leaves             │
  do I get per year?"              ▼
 ──POST /chat──▶          1. Auth check (JWT → user_id)
                              → cross-user access blocked here, before any search
                              │
                              ▼
                          2. Embed the question (same all-MiniLM-L6-v2 model)
                              │
                              ▼
                          3. Hybrid Search
                             ├─ Vector search (ChromaDB, meaning-based)  ─┐ weighted
                             └─ BM25 search   (exact keyword match)      ─┘ 0.6 / 0.4
                              │  filtered by vector_distance_threshold (0.75)
                              │  scoped to only this user's documents
                              ▼
                          4. Reranking (cross-encoder, top ~10 → top 3)
                             cross-encoder/ms-marco-MiniLM-L-6-v2
                             (question + chunk scored together, more precise)
                              │
                              ▼
                          5. Context Window Manager
                             dedupe overlapping chunks, cap at 4000 tokens
                              │
                              ▼
                          6. Prompt Builder → LLM.generate()
                             (Gemini gemini-3.6-flash, or Ollama llama3.1 —
                              chosen per-request by the frontend's Settings
                              toggle, falls back to LLM_PROVIDER if unset)
                              │
                              ▼           ← answer #1 generated
                          7. Hallucination Guard
                             SECOND LLM call: "is answer #1 grounded in
                             the retrieved context?" → {grounded, confidence}
                              │
                       not grounded? ──▶ regenerate with a stricter prompt
                              │              (THIRD LLM call, only if triggered)
                              ▼
                          8. Search Evaluator
                             grades best_score → "Excellent" / "Good" / "Weak"
                              │
                              ▼
                          9. Source Builder
                             attaches filename + chunk + score to the answer
                              │
                              ▼
                 ◀── JSON: { answer, sources[], search_evaluation } ──
 Browser renders:
   - the answer text
   - "Answered using: <filename>" per source, with % match
   - AnswerQualityBadge: "✓ Excellent match · 78%"
```

## The 9 stages of the query flow, in one line each

| # | Stage | Class / model | What it's for |
|---|---|---|---|
| 1 | Auth | JWT + `get_current_user` | Every downstream query is scoped to this user's own documents only |
| 2 | Query embedding | `all-MiniLM-L6-v2` | Turns the typed question into a 384-dim vector, comparable to stored chunks |
| 3 | Hybrid search | `HybridSearchService` (vector + `rank-bm25`) | Vector catches paraphrases, BM25 catches exact keywords; combined, weighted 0.6/0.4 |
| 4 | Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Re-scores the shortlist by reading question+chunk together — more accurate than step 3 alone, too slow to run on everything |
| 5 | Context management | `ContextWindowManager` | Dedupes overlapping chunks, stays under the LLM's token budget |
| 6 | Generation | `GeminiService` / `OllamaService` (via `AIServiceRegistry.get_llm(provider)`) | Writes the actual answer; which provider runs is chosen per-request (frontend Settings toggle), not fixed per server |
| 7 | Hallucination guard | `HallucinationGuardService` | A second LLM call checks the answer is actually supported by the context; regenerates with a stricter prompt if not |
| 8 | Search evaluation | `SearchEvaluator` | Grades the best match score into Excellent/Good/Weak, shown as a badge in the UI |
| 9 | Source attribution | `SourceBuilder` | Attaches filename + chunk + score so the answer is traceable back to the real document |

## Why this shape, in three sentences

**Ingestion is asynchronous** (upload returns instantly, a background
worker does the heavy parsing/chunking/embedding) so large documents never
risk an HTTP timeout. **Retrieval is two-stage** (cheap hybrid search
narrows thousands of chunks to ~10, an expensive reranker picks the true
best 3) because running the accurate-but-slow model on everything doesn't
scale. **Generation is self-checked** (a second LLM call validates the
first answer against the real retrieved text before it reaches the user)
because trusting an LLM's first answer outright risks a confident, wrong
response — this is what lets the system honestly say "I don't have enough
information" instead of guessing.

## Where things live

| Concern | Component |
|---|---|
| Structured data (users, documents, status) | PostgreSQL |
| Vectors (semantic search) | ChromaDB (its own server, HTTP) |
| Keyword index | BM25, in-process |
| Conversation history | In-memory only (not persisted) |
| LLM provider | Gemini (cloud) or Ollama (local) — chosen per-request; server default set by one config value, overridable per request from the frontend's Settings page |

See `docs/sprints/` for the full reasoning, real bugs found, and the
class-by-class "why" behind every piece above.
