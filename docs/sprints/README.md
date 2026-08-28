# Complete Sprint-by-Sprint Documentation

A full, honest technical history of this RAG chatbot's development — what
was built, why, how it actually works (with real examples), and what
genuinely broke along the way, verified rather than assumed. Written after
completing the full application (backend + frontend + deployment), based on
a systematic re-verification of the actual codebase, not from memory alone.

## Reading order

| # | File | Covers |
|---|---|---|
| 0 | [00-overview-and-architecture.md](00-overview-and-architecture.md) | Full architecture diagram, complete tech stack with real versions, the AI models actually used |
| 1 | [01-project-setup.md](01-project-setup.md) | Backend project structure, layered architecture |
| 2 | [02-document-upload.md](02-document-upload.md) | File upload, storage, UUID renaming |
| 3 | [03-document-parsing.md](03-document-parsing.md) | PDF/DOCX/TXT text extraction (PyMuPDF, python-docx) |
| 4 | [04-chunking-and-storage.md](04-chunking-and-storage.md) | Intelligent text splitting (LangChain), chunk metadata |
| 5 | [05-embeddings-and-ai-registry.md](05-embeddings-and-ai-registry.md) | Embedding generation (`all-MiniLM-L6-v2`), the singleton pattern |
| 6 | [06-vector-database-chromadb.md](06-vector-database-chromadb.md) | ChromaDB integration, embedded → server architecture evolution |
| 7 | [07-semantic-retrieval.md](07-semantic-retrieval.md) | Retrieval service, distance thresholds, centralized config |
| 8 | [08-llm-integration.md](08-llm-integration.md) | Gemini + Ollama, the provider abstraction pattern |
| 9 | [09-rag-pipeline-and-hybrid-search.md](09-rag-pipeline-and-hybrid-search.md) | Hybrid search, reranking, conversation memory, the hallucination guard |
| 10 | [10-authentication-and-multiuser.md](10-authentication-and-multiuser.md) | JWT auth, PostgreSQL, per-user document isolation, the bcrypt bug |
| 11 | [11-production-engineering-docker-ci.md](11-production-engineering-docker-ci.md) | Docker, GitHub Actions CI, the `libgomp1` and async-test bugs |
| 12 | [12-deployment-and-worker-queue.md](12-deployment-and-worker-queue.md) | Render deployment, background worker, **the ChromaDB concurrency bug** (the biggest single bug in this project) |
| 13 | [13-frontend-nextjs.md](13-frontend-nextjs.md) | The Next.js UI, scope decisions, real frontend bugs found and fixed |
| 14 | [14-bugs-and-lessons-learned.md](14-bugs-and-lessons-learned.md) | **Consolidated index of every real bug found across the whole project** — start here if you only read one file |

## How each file is structured

Every file follows the same format:
- **Objective** — what problem this sprint solved, and why it mattered at
  that point in the project
- **What we built** — real file paths, real code excerpts
- **Why we built it this way** — the actual reasoning, alternatives that
  were implicitly or explicitly rejected
- **How it works** — a concrete example walked through step by step, using
  real data from this project's own testing wherever possible
- **Positive scenarios** — what genuinely works, verified through direct
  testing during this project, not assumed
- **Negative scenarios / limitations** — honest gaps, edge cases, and real
  bugs, including ones that are still unresolved as of this writing

## The single most important file, if you only read one

[14-bugs-and-lessons-learned.md](14-bugs-and-lessons-learned.md) — because
software that "works" in a demo and software that's been genuinely stress-
tested under real, concurrent, production-like conditions are different
things, and this file is the honest record of the gap between those two.
