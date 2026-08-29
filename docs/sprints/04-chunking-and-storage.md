# Sprint 4 — Intelligent Chunking & Chunk Storage

## The example at this step

We now have one long string of text from `Employee_Leave_Policy.pdf`,
including the sentence: *"All full-time employees are entitled to 12 paid
sick leaves per calendar year, accrued monthly at 1 leave per month."*
A whole document can't be embedded as one single vector usefully —
embeddings work best on focused pieces of text. This step splits the
document into smaller "chunks," while making sure that exact sentence
doesn't get cut in half.

## What we built

**File:** `app/services/chunker.py`

```python
class ChunkingService:
    def __init__(self):
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,       # default 1000
            chunk_overlap=settings.chunk_overlap, # default 200
            length_function=len
        )

    def split(self, text, document_id, metadata):
        chunks = self.splitter.split_text(text)
        # wraps each piece as a DocumentChunk with an id like "14-0", "14-1"
```

## Classes & libraries used, and why

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `RecursiveCharacterTextSplitter` (LangChain) | Splits text near a target size, preferring paragraph breaks, then sentence breaks, then word breaks — only cutting mid-word as a last resort | Keeps the sick-leave sentence whole in one chunk instead of splitting `"...entitled to 12 paid"` \| `"sick leaves per year..."` across two chunks, which would make either half meaningless on its own | Splitting every fixed N characters (`text[0:1000]`, `text[1000:2000]`, …) is simpler but regularly cuts sentences and ideas in half, directly damaging retrieval quality later |
| `chunk_overlap=200` | Repeats the last 200 characters of one chunk at the start of the next | If a boundary happens to land right after "12 paid sick leaves," the overlap means the next chunk still carries that context instead of starting mid-thought | No overlap means a search that matches near a boundary can retrieve a chunk missing its own subject |
| `ChunkStorageService` | Writes each document's chunks to a flat JSON file, e.g. `chunks/14.json` | Useful for inspecting exactly what got chunked out of a document during development | This file is write-only — the real, load-bearing copy of each chunk lives in ChromaDB (Sprint 6) and the BM25 index (Sprint 9); this JSON file is a debugging aid, not a second source of truth |

## How it works — chunking Sarah's document

Given the parsed text
(`"Welcome to Acme Corp... Section 2: Leave Policy. All full-time
employees are entitled to 12 paid sick leaves per calendar year, accrued
monthly at 1 leave per month... Section 3: Benefits..."`), with
`chunk_size=1000, chunk_overlap=200`:

1. The splitter looks for a natural break (a paragraph boundary) near the
   1000-character mark.
2. It produces chunks like `chunk "14-0"` (Section 1 + start of Section
   2) and `chunk "14-1"` (the rest of Section 2, including the full
   sick-leave sentence, kept intact because it's short enough to stay
   inside one chunk boundary), each overlapping the previous by ~200
   characters.
3. Each chunk gets metadata attached:
   `{"document_id": "14", "user_id": "7", "filename": "<uuid>.pdf", "type": ".pdf", "chunk_id": "14-1"}`
   — this metadata travels with the chunk into ChromaDB (Sprint 6) and is
   what later powers per-user access filtering (Sprint 10) and source
   citations (Sprint 9).
4. `ChunkStorageService.save()` writes all of Sarah's document's chunks to
   `chunks/14.json` for inspection — the pipeline itself moves on to
   embedding (Sprint 5) using the in-memory chunk objects, not this file.

Chunk `"14-1"` — the one containing the sick-leave sentence — is the exact
chunk that gets embedded next, and is what Sarah's question will eventually
be matched against.
