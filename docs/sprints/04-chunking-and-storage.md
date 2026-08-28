# Sprint 4 — Intelligent Chunking & Chunk Storage

## Objective

A whole document's text (potentially thousands of words) can't be embedded
as a single vector usefully — embeddings work best on focused pieces of
text, and LLMs have context limits. We need to split documents into smaller
"chunks" — but naively (e.g., every 1000 characters) would cut sentences and
ideas in half, destroying meaning.

## What we built

**File:** `app/services/chunker.py`

```python
class ChunkingService:
    def __init__(self):
        # Deferred import - see Sprint 12 bugs doc for why
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,       # default 1000
            chunk_overlap=settings.chunk_overlap, # default 200
            length_function=len
        )

    def split(self, text, document_id, metadata):
        chunks = self.splitter.split_text(text)
        # ... wraps each piece as a DocumentChunk with an id like "14-0", "14-1"
```

**File:** `app/services/chunk_storage.py` — saves each document's chunks as a
JSON file, e.g. `chunks/14.json`.

## Why LangChain's `RecursiveCharacterTextSplitter`, and why "recursive"

The real problem with naive splitting:

> Bad: `"The company policy"` | `"allows employees"` — split mid-sentence,
> the two chunks individually don't mean much.
>
> Good: `"The company policy allows employees"` — kept together.

`RecursiveCharacterTextSplitter` tries a list of separators in order of
preference — paragraph breaks first, then sentence breaks, then word breaks,
only falling back to a hard character cut as a last resort. This means it
*prefers* natural breakpoints and only forces a cut when a piece is still
too long after trying those.

## Why `chunk_overlap=200`

Real scenario this solves: if a chunk boundary happens to fall in the middle
of an important idea (e.g., "Employees are entitled to 20 days of leave,
[CHUNK BOUNDARY] which must be requested two weeks in advance"), the second
half loses its subject without the overlap. A 200-character overlap means
the *end* of one chunk and the *start* of the next chunk share content,
so a search that matches near a boundary still gets full context.

## Why chunks are *also* saved as flat JSON files (`chunks/14.json`)

This turned out to be a documentation-worthy design characteristic, not
just a feature: **these JSON files are write-only.** Verified by grepping
the entire codebase for any code that reads them back — none exists. They
were written for debugging/inspection convenience during development, but
the actual running application never reads them again; the real "source of
truth" for retrieval is ChromaDB (Sprint 6) and the BM25 index (Sprint 9).
This is documented explicitly so a future maintainer doesn't assume these
files are load-bearing.

## How it works — a real walkthrough

Given the parsed text from Sprint 3
(`"Welcome to Acme Corp... Section 2: Leave Policy..."`), with
`chunk_size=1000, chunk_overlap=200`:

1. The splitter tries to find natural breaks (paragraphs) near the 1000-
   character mark.
2. Produces chunks like `chunk "14-0"`, `chunk "14-1"`, each ~1000
   characters, each overlapping the previous by ~200 characters.
3. Each chunk gets metadata attached:
   `{"document_id": "14", "user_id": "7", "filename": "<uuid>.txt", "type": ".txt", "chunk_id": "14-0"}`
   — this metadata travels with the chunk all the way into ChromaDB
   (Sprint 6) and is what powers per-user access filtering (Sprint 10) and
   source citations (Sprint 9).
4. `ChunkStorageService.save()` writes all chunks for this document to
   `chunks/14.json` (debug artifact, per above).

## Positive scenarios

- Real short documents (a single sentence, e.g. `"Artificial Intelligence"`)
  correctly produce exactly 1 chunk — verified live during this project.
- Real longer documents (multi-page PDFs) correctly split into multiple
  chunks with coherent boundaries, verified by inspecting actual chunk
  content during live testing (chunks read as complete thoughts, not
  cut-off fragments).

## Negative scenarios / limitations

- **A genuinely surprising, real bug found in this project:** simply
  *importing* `langchain_text_splitters` — regardless of which specific
  splitter class you actually use — pulls in `torch`, `transformers`, and
  `sentence_transformers` (roughly 3,900 additional Python modules),
  because the package's own `__init__.py` re-exports tokenizer-based
  splitters too. This meant "chunking" was accidentally as heavy an import
  as the ML embedding pipeline itself, which became a real production
  problem later (see Sprint 12 / bugs doc — this contributed to hitting
  Render's 512MB memory ceiling). Fixed by deferring the import to inside
  `ChunkingService.__init__` rather than the top of the file, so the cost
  is only paid when chunking is actually used, not at process boot.
- No overlap-aware deduplication — if a search matches two overlapping
  chunks, both are returned as if they were independent, slightly
  inflating apparent redundant context.
- Chunk size (1000 chars) is a single global setting — no per-document-type
  tuning (a dense legal document might benefit from smaller chunks than a
  narrative document).
