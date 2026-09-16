# Interview Guide

Short, interview-ready answers, specific to this project — not generic
RAG theory. Each answer references the real class/file so you can go
deeper if asked a follow-up.

## Architecture

**Explain your RAG architecture.**
Documents are uploaded, saved with a UUID filename, and processed
asynchronously by a separate worker process: parsed (PyMuPDF/python-docx),
split into overlapping chunks (LangChain's `RecursiveCharacterTextSplitter`),
embedded (`all-MiniLM-L6-v2`), and stored in both ChromaDB (vectors) and a
BM25 keyword index. A question goes through query rewriting and expansion,
hybrid retrieval (vector + BM25, weighted fusion), cross-encoder
reranking, then gets formatted into a prompt sent to an LLM (Gemini or
Ollama). A second LLM call checks the answer is actually grounded in the
retrieved context before it's returned, regenerating with a stricter
prompt if not.

**Walk me through what happens when a PDF is uploaded.**
`POST /upload` validates the extension, `StorageService` renames the file
to a UUID and saves it to disk, and a `Document` row is created with
`status="pending"` — the request returns immediately (`202`). Separately,
`app/worker.py` polls Postgres every 5 seconds; when it finds the pending
row, `DocumentProcessingService.process_document()` parses the text,
chunks it, embeds each chunk, writes the vectors to ChromaDB and the
chunks to the BM25 index, and flips `status` to `"completed"` (or
`"failed"` with the error message, on an exception).

**Walk me through what happens when a user asks a question.**
`RAGChatService.chat()`: checks the question doesn't reference another
user's data, rewrites it into a standalone query (accounting for
conversation history), expands it into 3 search-query variants, runs
hybrid retrieval for each variant against only the user's own documents,
merges and deduplicates the results, reranks with a cross-encoder, builds
a prompt from the top 3 chunks, generates an answer, validates it with a
second LLM call, and — if not grounded — regenerates once with a stricter
prompt before returning.

## Chunking

**Why do we chunk documents?**
An embedding model produces one vector per input — embedding a whole
document as one vector would blur every topic together, and it wouldn't
fit in an LLM's context window anyway. Smaller, focused chunks let
retrieval find the specific passage relevant to a question.

**Why use overlap?**
So a chunk boundary landing mid-idea doesn't strand the second half
without its subject. This project overlaps by 200 characters
(`chunk_overlap` in `app/core/config.py`) — the end of one chunk repeats
at the start of the next.

**What happens if chunks are too large?**
More context per chunk, but noisier retrieval matches (a large chunk can
contain the answer buried in a lot of unrelated text) and higher token
cost per chunk sent to the LLM.

**What happens if chunks are too small?**
More precise individual matches, but each chunk carries less surrounding
context, and you end up managing far more chunks per document.

## Embeddings

**What are embeddings?**
A list of numbers representing a piece of text's meaning — texts with
similar meaning produce vectors that are close together in that
numerical space, even if they use different words.

**Why use an embedding model?**
It's what makes semantic (meaning-based) search possible, as opposed to
matching only on exact keyword overlap.

**Why this model?**
`all-MiniLM-L6-v2` — small (~90MB), fast, runs on CPU, no GPU or paid API
needed. A real trade-off against a larger, more accurate model, made for
a project meant to run on modest infrastructure.

**How do query and document embeddings interact?**
Both are embedded by the exact same loaded model instance
(`EmbeddingService.generate()` for chunks,
`EmbeddingService.generate_query_embedding()` for questions) — comparing
vectors from two different models would be meaningless, since each model
has its own internal geometry.

## Vector DB

**Why Chroma?**
Purpose-built for fast nearest-neighbor vector search, and simple to run
as one more Docker Compose service alongside Postgres. It also runs as
its own server here (`HttpClient` over HTTP), not embedded in the app
process — a fix for a real concurrency bug when the web app and worker
both touched embedded storage at once.

**What is stored in Chroma?**
Per chunk: an ID (`"14-0"`), the chunk's plain text, its 384-float
embedding vector, and metadata (`document_id`, `user_id`, `filename`,
`chunk_id`, file type).

**What is similarity search?**
Given a query vector, find the stored vectors closest to it. This
project's Chroma collection is configured for L2 (Euclidean) distance,
converted to a 0–1 score with `1 / (1 + distance)`.

**What is top-k?**
How many results to return from a search. This project actually has
several different top-k values at different stages — `top_k_vector`
(10), `top_k_bm25` (10), `hybrid_top_k` (10), `retrieval_top_k` (5), and
a final hardcoded top-3 after reranking — not one single number.

## Retrieval

**How does `RetrievalService` work?**
It has three methods: `retrieve()` (low-level — given a query embedding
and known document IDs, runs hybrid search and filters by score),
`retrieve_for_user()` (resolves a user's document IDs from Postgres, then
calls `retrieve()` — used by `/search`), and `multi_retrieve()` (resolves
document IDs once, then calls `retrieve()` once per expanded query and
merges/deduplicates — used by `/chat`).

**How do you improve retrieval quality?**
In this specific codebase: tune `vector_weight`/`bm25_weight`,
`hybrid_score_threshold`, or `reranker_score_threshold`; chunk size/
overlap; or add an evaluation set (Recall@K, MRR) to measure changes
objectively — none of which currently exists here.

**What is hybrid search?**
Combining semantic (vector) search with keyword (BM25) search and
merging the results — this project does it with a weighted sum of
normalized scores (`0.6 * vector_score + 0.4 * bm25_score`), not
Reciprocal Rank Fusion.

**Why combine vector and keyword search?**
Vector search catches paraphrased questions (different words, same
meaning); it can under-rank a chunk that contains an exact rare term
(an ID, a product code) that BM25 would catch directly. Combining both
covers more real questions correctly than either alone.

**What is BM25?**
A classic keyword-ranking algorithm that scores a document by how well
its term frequencies match the query terms, with penalties for document
length. Implemented here via `rank-bm25`'s `BM25Okapi`, tokenized by
lowercasing and splitting on whitespace.

**What is RRF?**
Reciprocal Rank Fusion — combines two ranked lists by each item's *rank
position* (`score = Σ 1/(k + rank)`) rather than by raw score, which
avoids needing to normalize two differently-scaled scoring systems onto
a comparable range. This project does **not** use RRF — it normalizes
raw scores directly and combines them with fixed weights instead.

**What is reranking?**
A second, more precise (and more expensive) relevance pass, run only on
the retrieval shortlist. This project's `Reranker` uses a cross-encoder
(`cross-encoder/ms-marco-MiniLM-L-6-v2`) that reads the query and a
candidate chunk *together*, which is more accurate than the independent
scoring embedding-based search does, but too slow to run against every
stored chunk.

## LLM

**Why use RAG instead of fine-tuning?**
Fine-tuning changes a model's weights/style, not its access to specific,
easily-updated facts — a newly uploaded document would need retraining
to be usable. RAG retrieves the relevant content at request time and
puts it directly in the prompt, so a document is answerable immediately
after it's processed, with no training step.

**How is context passed to the LLM?**
`ContextFormatter.format()` builds a labeled text block (`SOURCE N /
Document / Chunk ID / Similarity Score / Content`, joined across sources)
which `PromptBuilder.build()` inserts into a fixed prompt template
alongside conversation history and the question.

**How do you reduce hallucinations?**
Three real mechanisms in this codebase: (1) the prompt explicitly
instructs the model to answer only from context and to say a specific
fallback sentence if the answer isn't there; (2) a distance/relevance
threshold means genuinely irrelevant chunks are dropped before ever
reaching the prompt, rather than always forcing in a "top-3" regardless
of quality; (3) `HallucinationGuardService` makes a second LLM call that
checks the generated answer against the actual retrieved context and
triggers a stricter regeneration if it isn't grounded.

**How would you handle very large context?**
Currently `ContextWindowManager` estimates size by word count (not real
tokens — `tiktoken` is installed but unused) and simply stops adding
chunks once a budget is hit; nothing is summarized or truncated within a
chunk. A more robust version would use a real tokenizer for the specific
model in use and possibly summarize lower-priority chunks instead of
dropping them outright.

**How would you stream responses?**
This project already has `POST /chat/stream`, but it reveals the
*already-fully-generated and validated* answer word-by-word over
Server-Sent Events — not real token-level LLM streaming, because the
hallucination guard needs the complete answer before it can validate it.
True token streaming would mean either streaming an unvalidated draft, or
accepting that validation happens after the user has already seen the
answer.

## Production

**What happens with 1 million documents?**
The BM25 index (`rank-bm25`, in-process, pickled, rebuilt from scratch on
every change) is the first thing that breaks down — it doesn't scale to
that volume or update efficiently. ChromaDB itself can hold far more
vectors, but a single unreplicated instance becomes a real bottleneck and
single point of failure at that scale.

**How would you scale ingestion?**
Replace the 5-second polling loop with a real message queue (SQS,
RabbitMQ, etc.) so processing starts immediately and multiple worker
replicas can consume from it in parallel, and move uploaded files to
object storage instead of a local disk volume shared between containers.

**How would you support multiple users?**
Already implemented at the user level — every document has a `user_id`,
every retrieval call resolves and filters by the requesting user's
document IDs before searching. What's *not* implemented is
multi-tenancy (organizations/workspaces) or document sharing between
users.

**How would you isolate user documents?**
This project already does, structurally: `DocumentRepository` never
returns a document belonging to another user (`403` either way, so an
attacker can't distinguish "doesn't exist" from "not yours"), and
`RetrievalService` resolves the user's own document IDs *before* running
any vector or BM25 search, rather than filtering a shared result set
afterward.

**How would you evaluate retrieval quality?**
Build a labeled set of (question, correct chunk/document) pairs and
measure Recall@K, Precision@K, MRR, and NDCG against it — none of which
exists in this codebase today; the only "evaluation" present is a
per-request relevance label (Excellent/Good/Weak) shown to the user, not
an offline quality benchmark.

**How would you monitor hallucinations?**
`RAGMetrics` already logs `hallucination_detected` and
`hallucination_check_time` per request (`MetricsService.record()`) — but
only to a log file, not to any metrics/alerting system. In production,
you'd export that as a real metric (e.g. hallucination rate over time)
to a monitoring system and alert on spikes.
