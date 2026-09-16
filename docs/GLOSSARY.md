# Glossary

Plain-language definitions of terms used throughout this documentation.

**RAG (Retrieval-Augmented Generation)** — an approach where an LLM's
answer is grounded by first retrieving relevant text from a knowledge
source (here: a user's uploaded documents) and including it in the
prompt, instead of relying only on the model's training data.

**Retrieval** — the process of finding the most relevant stored chunks
for a given question, out of everything stored.

**Augmented Generation** — the "generation" step (an LLM writing an
answer) made more accurate by "augmenting" the prompt with retrieved
context first.

**Embedding** — a list of numbers representing the meaning of a piece of
text, produced by an embedding model. This project uses 384-number
embeddings from `all-MiniLM-L6-v2`.

**Vector** — the mathematical term for that list of numbers; "embedding"
and "vector" are used interchangeably here.

**Vector Database** — a database built to store vectors and answer
"which stored vectors are closest to this one?" efficiently. This
project uses ChromaDB.

**Chunk** — one piece of a document, small enough to embed and retrieve
meaningfully, produced by splitting the full document text.

**Chunk Size** — the target length of each chunk. This project uses 1000
characters.

**Overlap** — shared text repeated between the end of one chunk and the
start of the next, so a chunk boundary doesn't strand an idea without its
context. This project uses 200 characters.

**Similarity** — how close two vectors are to each other; used as a
proxy for how related two pieces of text are in meaning.

**Cosine Similarity** — a specific similarity formula,
`(A · B) / (||A|| × ||B||)`, measuring the angle between two vectors.
Not what this project actually computes (it uses L2 distance, converted
to a score) — included here because it's the formula most commonly
associated with embedding search in general.

**Top-K** — how many top-ranked results to return from a search. This
project has several different top-K values at different pipeline stages.

**Context** — the retrieved text handed to the LLM alongside the
question, so it can answer from real source material.

**Context Window** — the maximum amount of text (input + output) a
given LLM can process in one call. This project approximates its own
context budget by word count, not the model's real token limit.

**LLM (Large Language Model)** — the model that generates the final
natural-language answer. This project supports Gemini and Ollama.

**Prompt** — the full text sent to the LLM: instructions, conversation
history, retrieved context, and the question, assembled in that order by
`PromptBuilder`.

**Grounding** — making sure an LLM's answer is actually supported by the
provided context, rather than the model's own general knowledge or a
guess. Enforced here by prompt instructions plus a second LLM call that
checks the answer afterward.

**Hallucination** — when an LLM states something as fact that isn't
actually supported by the given context (or is simply false). This
project's `HallucinationGuardService` checks for this and can trigger a
stricter regeneration.

**Semantic Search** — search based on meaning (via embeddings), able to
match a paraphrased question to relevant text even with no shared exact
words.

**Keyword Search** — search based on matching exact terms. This project
implements it via BM25.

**BM25** — a classic keyword-ranking algorithm that scores documents by
term-frequency match against a query, with adjustments for document
length. Implemented here via the `rank-bm25` library's `BM25Okapi`.

**Hybrid Search** — combining semantic and keyword search and merging
their results, to catch both paraphrased questions and exact-term
matches. Genuinely implemented in this project (weighted-sum fusion, not
Reciprocal Rank Fusion).

**Reranking** — a second, more precise (and more expensive) relevance
pass run only on a retrieval shortlist, to reorder results more
accurately than the first-pass search could. Implemented here via a
cross-encoder.

**Cross Encoder** — a model that scores a query and a candidate text
*together*, jointly, rather than comparing two independently-computed
embeddings — more accurate, but too slow to run against a whole
collection, which is why it's only used on the shortlist.

**Metadata** — extra structured data attached to a chunk (document ID,
user ID, filename, chunk ID) alongside its text and vector, used for
filtering (e.g. restricting search to one user's documents).

**Collection** — a named group of vectors in ChromaDB. This project uses
a single collection, `"documents"`, shared by every user and document.

**Retriever** — the component responsible for turning a query into a set
of relevant chunks. In this project, that's `RetrievalService` (wrapping
`HybridSearchService`).

**Embedding Model** — the model that converts text into a vector. This
project uses `all-MiniLM-L6-v2` for both documents and queries.

**Inference** — running a trained model to produce an output (an
embedding, a rerank score, or a generated answer), as opposed to training
it. No training happens anywhere in this project — every model call is
inference.

**Token** — the unit a language model actually processes text in
(roughly a word or word-piece, not exactly a character or a whole word).
This project's own context-budget estimate does not use real tokens — it
counts words instead.
