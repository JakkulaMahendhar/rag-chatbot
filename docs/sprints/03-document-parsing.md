# Sprint 3 — Document Parsing

## Objective

A PDF or DOCX file is a binary format — it's not just "text with some
formatting." Before anything else can happen (chunking, embedding), we need
to extract *plain text* from these binary containers.

## What we built

**File:** `app/services/parser.py`

```python
class ParserService:
    @staticmethod
    def parse(file_path: Path) -> str:
        extension = file_path.suffix.lower()
        if extension == ".pdf":
            return ParserService.parse_pdf(file_path)
        if extension == ".docx":
            return ParserService.parse_docx(file_path)
        if extension == ".txt":
            return ParserService.parse_txt(file_path)
        raise ValueError("Unsupported document type")

    @staticmethod
    def parse_pdf(file_path: Path) -> str:
        document = fitz.open(file_path)          # PyMuPDF
        text = ""
        for page in document:
            text += page.get_text()
        document.close()
        return text
```

## Why PyMuPDF (imported as `fitz`) for PDFs

PDF text extraction is notoriously inconsistent across libraries — some PDFs
have text as real selectable text, others are scanned images (no extractable
text at all), others have text in a strange internal order. PyMuPDF was
chosen because it:
- Handles the vast majority of "normal" PDFs (text-based, not scanned
  images) correctly and fast
- Is actively maintained and widely used in production systems
- Does *not* attempt OCR (optical character recognition) — a deliberate
  scope boundary: this project extracts text that already exists in the
  file, it does not read text out of images

## Why python-docx for Word documents

`python-docx` reads the actual paragraph structure of a `.docx` file (which
is really a ZIP archive of XML files internally) and gives clean paragraph
text, joined with `"\n".join(paragraphs)`.

## A real, important limitation this creates (see Sprint 9 for the consequence)

**PDF page boundaries are lost.** Look closely at `parse_pdf`:
```python
text = ""
for page in document:
    text += page.get_text()
```
Every page's text is concatenated into **one single string** with no marker
for where one page ends and the next begins. This was a deliberate
simplification at the time, but it had a real, confirmed downstream
consequence: **this system cannot cite page numbers in its answers.** When
the frontend (much later) needed to show "which page is this answer from,"
the honest answer — verified by reading this exact code — is: it can't,
because the information was thrown away at the parsing stage. The frontend
documentation (`docs/sprints/13-frontend-nextjs.md`) explicitly documents
this as a "don't invent data" decision: rather than fabricate a fake page
number, the UI shows filename + relevance score only.

## How it works — a real walkthrough

1. `employee-handbook.pdf` (3 pages) arrives from Sprint 2's upload.
2. `ParserService.parse()` detects the `.pdf` extension.
3. PyMuPDF opens the file, iterates all 3 pages, concatenates their text.
4. Returns one long string like:
   `"Welcome to Acme Corp...  [page 1 content]  Section 2: Leave Policy...
   [page 2 content]  Section 3: Benefits...  [page 3 content]"`
   — with no indication where page 1 ends and page 2 begins.

## Positive scenarios

- Correctly extracts text from standard, text-based PDFs and DOCX files —
  verified repeatedly during this project with real uploaded test documents.
- Fast — no OCR or heavy processing, just structural extraction.
- Clean abstraction: `ParserService.parse()` is the *only* thing the rest of
  the pipeline needs to call; it doesn't need to know PDF vs DOCX internals.

## Negative scenarios / limitations

- **Scanned/image-only PDFs return empty or near-empty text** — there's no
  OCR fallback. A scanned contract with no embedded text layer would
  silently produce a document with ~0 usable chunks.
- **No page number tracking** (explained above) — a real, confirmed
  limitation, not a hypothetical one.
- **No table structure preservation** — PyMuPDF's `get_text()` extracts
  text in reading order but doesn't preserve table rows/columns as
  structured data; a table becomes a jumble of text that may not read
  coherently out of context.
- **Corrupted or password-protected files** raise an exception (caught
  higher up by `DocumentProcessingException`, see Sprint 12's worker docs)
  rather than partially succeeding.
