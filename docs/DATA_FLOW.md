# Data Flow

Visual reference for how data moves through the system. See
[`docs/RAG_PIPELINE.md`](RAG_PIPELINE.md) for the explanation behind each
step, and [`docs/diagrams/`](diagrams/) for these same diagrams as
standalone `.mmd` files.

## Document Ingestion Flow

```mermaid
flowchart TD
    File[Uploaded file] --> Validate["Extension check\n(.pdf / .docx / .txt)"]
    Validate --> Store["StorageService.save_file()\nUUID rename, uploads/"]
    Store --> PGPending[("PostgreSQL\nstatus = pending")]
    PGPending -. worker polls every 5s .-> Parser["ParserService.parse()\nPyMuPDF / python-docx / open()"]
    Parser --> Text[Plain text]
    Text --> Chunks["ChunkingService.split()\nchunk_size=1000, overlap=200"]
    Chunks --> Embed["EmbeddingService.generate()\nall-MiniLM-L6-v2"]
    Embed --> Vectors[384-dim vectors]
    Vectors --> ChromaDB[("ChromaDB\ncollection: documents")]
    Chunks --> BM25[("BM25 index\npickled to disk")]
    ChromaDB --> PGDone[("PostgreSQL\nstatus = completed")]
    BM25 --> PGDone
```

## Query Flow

```mermaid
flowchart TD
    Question[User question] --> Access["QueryAccessService\ncross-user check"]
    Access --> Enhance["QueryEnhancer\nLLM call: standalone query"]
    Enhance --> Expand["QueryExpander\nLLM call: 3 query variants"]
    Expand --> Loop["For each variant:\nembed + hybrid search"]
    Loop --> Merge["Merge + deduplicate\nby chunk_id"]
    Merge --> Rerank["Reranker (CrossEncoder)\ntop 3 above threshold"]
    Rerank --> Dedup[ContextDeduplicator]
    Dedup --> Compress[ContextCompressor]
    Compress --> Window[ContextWindowManager]
    Window --> Format[ContextFormatter]
    Format --> Prompt[PromptBuilder]
    Prompt --> Gen["LLM.generate()\nGemini or Ollama"]
    Gen --> Guard["HallucinationGuardService\nLLM call: grounded check"]
    Guard -->|not grounded| Regen["LLM.generate()\nstricter prompt"]
    Guard -->|grounded| Answer[Final answer]
    Regen --> Answer
    Answer --> Response["JSON response, or\nSSE stream (/chat/stream)"]
```

## Complete Flow

```mermaid
flowchart TD
    subgraph Ingest["Ingestion (background worker)"]
        U[Upload] --> P[Parse] --> C[Chunk] --> E[Embed]
        E --> V[(ChromaDB)]
        E --> B[(BM25)]
    end

    subgraph Query["Query (POST /chat)"]
        Q[Question] --> QR[Rewrite + Expand]
        QR --> H[Hybrid Search]
        V -.-> H
        B -.-> H
        H --> R[Rerank]
        R --> Ctx[Build Context]
        Ctx --> L[LLM Generate]
        L --> G[Hallucination Guard]
        G --> A[Answer]
    end

    Ingest -.stored vectors available to.-> Query
```

## Notes on what's shown vs. simplified

- The "Loop" step in the query-flow diagram runs the full hybrid-search
  path (vector + BM25 + fusion + threshold filter) **once per expanded
  query** (3 variants by default) — shown as one box for readability; see
  [`docs/RETRIEVAL.md`](RETRIEVAL.md) for the unrolled version.
- The hallucination guard's regeneration path is a real conditional
  branch, not decorative — it only fires when the guard's LLM call
  returns `grounded: false`.
- Ingestion and query are entirely separate flows running in separate
  processes (worker vs. web app) — the diagrams are drawn separately
  because they don't share a call stack, only shared storage (ChromaDB,
  BM25 index, Postgres).
