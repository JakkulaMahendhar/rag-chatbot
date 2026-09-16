# Industry Alternatives

What this project actually uses, compared against other options commonly
used for the same job. No ranking — the right choice depends on scale,
budget, existing infrastructure, and data residency requirements that
this document doesn't know about.

| RAG Layer | Current Project | Alternatives | Why Alternatives Are Used |
|---|---|---|---|
| **Document parsing** | PyMuPDF (PDF), python-docx (DOCX) | Unstructured (handles many formats + layout-aware chunking), Apache Tika, Azure Document Intelligence, AWS Textract | Scanned/image documents need OCR (none of PyMuPDF/python-docx do this); tables and complex layouts need layout-aware extraction |
| **Chunking** | `RecursiveCharacterTextSplitter` (character/token-count based) | Semantic chunking (split where embedding similarity changes), structure-aware chunking (split by detected headings/sections) | Character-count splitting can cut a coherent idea in half if it happens to land mid-topic; structure/semantic-aware splitting respects the document's actual organization |
| **Embeddings** | `sentence-transformers` / `all-MiniLM-L6-v2` (local, 384-dim) | OpenAI `text-embedding-3-*`, Cohere `embed-*`, Voyage AI, BGE, E5 | Higher accuracy (larger models), managed infrastructure (no local model to run), built-in multilingual support |
| **Vector DB** | ChromaDB (self-hosted server) | Pinecone, Qdrant, Weaviate, Milvus, `pgvector`, Elasticsearch/OpenSearch | Larger scale, managed hosting, richer filtering, or (for `pgvector`) avoiding a second database when Postgres is already in use |
| **Keyword search** | `rank-bm25` (in-process, pickled to disk) | Elasticsearch, OpenSearch | A distributed, persistent, independently-scalable keyword index instead of an in-process pickle that's fully rebuilt on every change |
| **Hybrid fusion** | Weighted-sum of normalized scores | Reciprocal Rank Fusion (RRF), native hybrid search in Qdrant/Weaviate | RRF combines by rank position instead of raw score, which avoids needing to hand-tune score normalization and weights |
| **Reranking** | Cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`, local) | Cohere Rerank (hosted API), BGE reranker, LLM-based reranking | Hosted rerankers avoid running the model locally; LLM-based reranking can reason about relevance more flexibly at higher cost/latency |
| **LLM** | Gemini (`gemini-3.6-flash`) / Ollama (`llama3.1`, local) | OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, self-hosted (vLLM, etc.) | Different cost structures, data-residency requirements, and quality/latency trade-offs |
| **API framework** | FastAPI | Flask, Django, Express (Node), Spring Boot (Java) | Team language/framework preference, existing infrastructure, or feature needs (e.g. Django's built-in admin) |

## Where this project's choices genuinely stand out

- **Hybrid search is real here**, not a stated-but-unimplemented feature
  — many portfolio RAG projects only do vector search. See
  [`docs/RETRIEVAL.md`](RETRIEVAL.md).
- **Reranking is real here too.** Combined with hybrid search and a
  hallucination guard, this is a more complete pipeline than "embed,
  search, stuff into a prompt."
- **The vector database runs as its own server process**, not embedded
  in the web process — a deliberate choice made after a real concurrency
  bug (see [`docs/sprints/06-vector-database-chromadb.md`](sprints/06-vector-database-chromadb.md)),
  which is the same operational pattern production vector databases use.

## Where this project is simpler than an industry deployment

- One BM25 index, rebuilt from scratch on every change, in a single
  process — not a distributed, incrementally-updated keyword store.
- No managed/hosted equivalents anywhere — every component (Postgres,
  ChromaDB, the embedding model, the reranker) runs as a container or
  in-process, not a managed cloud service (aside from the LLM API calls
  themselves).
- Fusion is hand-tuned weights, not RRF or a learned fusion model.

See [`docs/PRODUCTION_EVOLUTION.md`](PRODUCTION_EVOLUTION.md) for what
would specifically change to close these gaps at real scale.
