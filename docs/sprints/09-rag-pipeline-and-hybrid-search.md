# Sprint 9 — The Complete RAG Pipeline: Hybrid Search, Reranking, Conversation Memory, Hallucination Guard

## The example at this step

Sarah asks: *"How many sick leaves do I get per year?"* This sprint is
where five separate mechanisms combine to turn that question into a
trustworthy answer: searching by both meaning and exact keywords, a second
pass that re-scores results for true relevance, remembering earlier
messages in the conversation, and a second LLM call that checks the first
answer before it's shown to Sarah.

## 1. Hybrid Search — combining vector + keyword search

**File:** `app/services/hybrid_search.py`

```python
def search(self, ...):
    vector_results = self.vector_store.search(...)
    bm25_results = self.bm25_service.search(...)
    # combined with weights: vector_weight=0.6, bm25_weight=0.4
```

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| **Vector search** (Sprint 6/7) | Finds chunks close in *meaning* to Sarah's question | Catches paraphrased questions — Sarah could ask "how much time off do I get if I'm sick" and still match the same chunk, because the *meaning* is close even though the words differ | On its own, it can sometimes rank a topically-related-but-wrong chunk above a chunk that contains the literal exact phrase Sarah used |
| **BM25** (`rank-bm25` library, `app/services/bm25_search.py`) | A classic keyword-search algorithm — scores chunks by exact term overlap | Sarah's question literally contains the words "sick leaves" — BM25 is excellent at rewarding chunks that contain that exact phrase, which vector search alone might under-rank | On its own, BM25 sees "leave policy" and "vacation days" as unrelated word sets — it has no concept of meaning, only exact terms |
| `vector_weight=0.6` / `bm25_weight=0.4` | Combines both scores into one, trusting vector search slightly more | Gives the best of both: catches Sarah's exact phrase *and* would still work if she'd paraphrased it | Using only one method means picking which failure mode you're willing to accept; combining both, weighted, covers more real questions correctly |

Scores from both methods are normalized to a 0–1 range before combining:
```python
return 1.0 / (1.0 + distance)   # converts ChromaDB's raw distance into a 0-1 similarity
```
This exact formula is reused as-is by the frontend (Sprint 13) to display
a relevance percentage — calculated in one place, not reinvented twice.

## 2. Reranking — a second, more precise scoring pass

**File:** `app/services/reranker.py`, model:
`cross-encoder/ms-marco-MiniLM-L-6-v2`

```python
class Reranker:
    def rerank(self, query, documents):
        pairs = [[query, doc.content] for doc in documents]
        scores = self.model.predict(pairs)
        for doc, score in zip(documents, scores):
            doc.rerank_score = 1 / (1 + math.exp(-float(score)))  # sigmoid
        return sorted(documents, key=lambda x: x.rerank_score, reverse=True)[:3]
```

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")` | Looks at Sarah's question *and* a candidate chunk together, jointly, and scores how relevant that specific pairing is | Far more accurate than comparing two independently-computed vectors, because the model actually reads the question and the chunk side by side | Too slow to run against every chunk in a large document set — which is exactly why hybrid search (above) narrows thousands of chunks down to ~10 candidates first, and only those 10 get this more expensive, more precise pass |
| `AIServiceRegistry.get_reranker()` | Loads the `CrossEncoder` once per process and hands the same instance to every chat request | The cross-encoder is loaded from disk exactly like the embedding model (Sprint 5) — reusing the same singleton pattern means Sarah's second and third questions don't each pay a multi-second model-load cost | `RAGChatService` originally called `Reranker()` directly on every request, reloading the model from disk every time; this was found and fixed after real timing logs showed several extra seconds on every single chat message — see [Sprint 5](05-embeddings-and-ai-registry.md) for the fix and [the bugs doc](14-bugs-and-lessons-learned.md) for the measured before/after |

This two-stage pattern — fast broad retrieval, then a slower precise
re-score of just the finalists — is a standard information-retrieval
technique: use the cheap method to shortlist, the expensive method to pick
the winner. For Sarah's question, the sick-leave chunk (already a strong
hybrid-search match) is confirmed and pushed to the top by the
cross-encoder's more careful read of the actual pairing.

## 3. Conversation Memory — multi-turn context

**File:** `app/services/conversation_store/memory.py`

```python
class InMemoryConversationStore(ConversationStore):
    def __init__(self):
        self.store = {}   # {conversation_id: [messages]}
```

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `InMemoryConversationStore` | Keeps each conversation's message history in a Python dictionary, in process memory | Simple, and enough for follow-up questions within one session — if Sarah asks "and how do I request it?" right after, the conversation ID lets that follow-up be answered with the earlier context still in mind | A database-backed conversation table would additionally survive server restarts and support listing past conversations — a real, separate feature this project doesn't currently implement, since it wasn't in scope for the chat feature itself |

## 4. Hallucination Guard — checking the answer before Sarah sees it

**File:** `app/services/hallucination_guard_service.py`

```
1. Gemini generates an initial answer from the retrieved sick-leave chunk.
2. A SECOND Gemini call asks: "is this answer fully supported by the context?"
   returning JSON: {"grounded": true/false, "confidence": 0-1, "unsupported_claims": []}
3. IF NOT grounded:
   → re-generates the answer using a STRICTER prompt that explicitly
     instructs: 'If information is missing say: "I don't have enough
     information."'
```

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `HallucinationGuardService.validate()` | Makes a second, independent LLM call whose only job is to check the first answer against the actual retrieved text | For Sarah's sick-leave question, the answer "12 paid sick leaves per year" is directly stated in the retrieved chunk, so this passes as grounded. If Sarah instead asked something the document never covers (e.g. "can I carry over unused sick leave to next year?"), an LLM might otherwise guess plausibly — this second pass catches that and forces an honest "I don't have enough information" instead | Trusting the first generated answer outright is faster and cheaper, but has no defense against the LLM confidently making something up when the retrieved context doesn't actually contain the answer |

This is a genuine two-pass mechanism, not just a prompt instruction. When
it triggers a regeneration, one user question results in **three separate
LLM calls** (generate → validate → regenerate) — a real cost and latency
tradeoff made deliberately in exchange for a much lower chance of Sarah
being told something false about her own leave policy.

### A real bug: Gemini's JSON always failed to parse, so the guard always regenerated

`_parse_response()` originally called `json.loads(response)` directly on
whatever the validation call returned. Gemini, even when the prompt says
*"Return only JSON"*, reliably wraps its answer in a markdown code fence —
` ```json\n{...}\n``` ` — which `json.loads()` rejects outright. That sent
every single Gemini validation straight into the `except` branch, which
returns a hardcoded `{"grounded": false, "confidence": 0,
"unsupported_claims": ["Unable to validate response"]}` — meaning **every
Gemini answer was reported as ungrounded**, correct or not, and **every
Gemini chat message paid for a needless regenerate call** it didn't
actually need. `app/services/query_expander.py`'s `QueryExpander` (used
earlier in the same request, to generate search-query variations) already
stripped this exact fence before parsing its own JSON — this file just
hadn't been given the same fix yet. `_parse_response()` now strips a
leading/trailing ` ``` ` (and an
optional `json` language tag) before calling `json.loads()`, mirroring
`QueryExpander`'s approach. Verified live: the same question that used to
log `{'grounded': False, ...}` on every Gemini call now correctly logs
`{'grounded': True, 'confidence': 1, 'unsupported_claims': []}`.

## 5. Source Citations & Context Window Management

**Files:** `app/services/source_builder.py`, `app/services/context_window_manager.py`, `app/services/context_formatter.py`, `app/services/prompt_builder.py`

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `SourceBuilder` | Converts raw retrieval results into `SourceReference` objects (`document_id`, `chunk_id`, `filename`, `content`, `score`) returned alongside the answer | Lets Sarah's chat UI show *"Answered using: Employee_Leave_Policy.pdf"* instead of an answer with no traceable source | Returning only the generated text with no source reference would make it impossible for Sarah to verify the answer against her own document |
| `ContextWindowManager` | Deduplicates overlapping chunks and stays under a token budget (`max_context_tokens=4000`) before building the LLM prompt | LLMs have a finite context window; naively stuffing every retrieved chunk into the prompt could exceed it or waste tokens on redundant, overlapping text | — |
| `ContextFormatter` | Turns the retrieved chunks into a labeled block of text — `SOURCE 1 / Document: ... / Chunk ID: ... / Similarity Score: ... / Content: ...` — for the LLM to read | Gives the LLM a clear, structured view of *where* each piece of context came from, which helps it judge relevance and avoid blending unrelated chunks | Concatenating raw chunk text with no structure makes it harder for the model to tell where one source ends and another begins |
| `PromptBuilder` | Assembles the final prompt: system instructions, conversation history, the formatted context, and the question | One place that defines exactly what the LLM sees and is told to do, rather than string-building scattered across the codebase | — |

### A real bug: the LLM was echoing the internal SOURCE/Chunk ID labels back into its answer

`ContextFormatter`'s labels (`SOURCE 1`, `Chunk ID: 6-6`, `Similarity
Score: 0.72`) are meant purely for the LLM's own internal reference — they
were never supposed to appear in the text Sarah actually reads. But
`PromptBuilder`'s original rules never said that. Asked a broad question
like *"Explain about Machine Learning and those important concepts,"*
Ollama's `llama3.1` (less strict than Gemini about subtle formatting
instructions) sometimes just copied the labels straight into its answer:
*"Machine learning ... (Source 2, Chunk ID: 6-6, Content: 1.1 What Is
Machine Learning?)"* — reading like a raw context dump instead of a
written answer. Added an explicit rule to both `PromptBuilder` and the
hallucination guard's strict regeneration prompt: the labels are for
reference only, never to be repeated — Sarah already sees real source
attribution separately, via `SourceBuilder` and the frontend's
`AnswerQualityBadge` (Sprint 13), so the LLM never needed to reproduce it
inline. Verified against the same broad question afterward: clean prose,
no label leakage.

## 6. Search Evaluation — grading the answer, not just generating it

**File:** `app/services/search_evaluator.py`

```python
class SearchEvaluator:
    @staticmethod
    def evaluate(question, sources):
        scores = [s.score for s in sources if s.score is not None]
        best_score = max(scores)
        if best_score >= 0.7:
            quality = "Excellent"
        elif best_score >= 0.5:
            quality = "Good"
        else:
            quality = "Weak"
        return {"question": question, "best_score": best_score, "quality": quality, ...}
```

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `SearchEvaluator.evaluate()` | Grades the best-matched source's similarity score into a plain label — `Excellent` (≥0.7), `Good` (≥0.5), or `Weak` (below that) | Sarah has no way to judge, from the generated sentence alone, whether the answer came from a strong match in her document or a weak, borderline one — this turns the raw score into something she can glance at instantly | A raw number like `0.765` means nothing without context; a fixed label with clear thresholds is something a non-technical user can trust at a glance |

This was computed and returned by `POST /chat` from the moment this
sprint was built — but wasn't read by anything for a while. The frontend
(Sprint 13) later added `AnswerQualityBadge`, which is what finally
displays it to Sarah.

## How the whole pipeline connects, for Sarah's one question

Question → embed → hybrid search (vector + BM25) finds chunk `"14-1"` as
the top candidate → reranker confirms it's the most relevant of the
shortlist → `ContextWindowManager` builds a clean prompt → Gemini generates
*"You are entitled to 12 paid sick leaves per year, accrued at 1 per
month"* → the hallucination guard checks that claim against chunk `"14-1"`
and confirms it's grounded → `SourceBuilder` attaches the source →
`SearchEvaluator` grades the match (`0.765` → `"Excellent"`) → the answer,
its source, and its quality label are all returned to Sarah together.
