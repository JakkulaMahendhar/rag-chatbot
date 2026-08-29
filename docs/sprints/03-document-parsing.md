# Sprint 3 — Document Parsing

## The example at this step

`Employee_Leave_Policy.pdf` is now sitting on disk as a binary PDF file.
A PDF is not "text with some formatting" — it's a binary container. Before
anything else can happen, the plain text (including the sick-leave
sentence on page 2) has to be pulled out of it.

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

## Classes & libraries used, and why

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| **PyMuPDF** (imported as `fitz`) | Opens a PDF and extracts its plain text, page by page | Fast, actively maintained, and correctly handles the vast majority of normal (non-scanned) PDFs like Acme Corp's policy document | `PyPDF2` is more commonly known but slower and less reliable on real-world PDFs with complex layouts; full OCR libraries (e.g. Tesseract) are far heavier and unnecessary for a PDF that already has real text in it, like this one |
| **python-docx** | Reads the paragraph structure of a `.docx` file (internally a ZIP of XML files) | Gives clean, already-separated paragraph text via `"\n".join(paragraphs)` | Manually unzipping and parsing the XML would reproduce what this library already does correctly |
| `ParserService.parse()` | One entry point that picks the right extraction method by file extension | The rest of the pipeline (chunking, embedding) calls one function and never needs to know if the source was a PDF or a DOCX | Calling `parse_pdf()`/`parse_docx()` directly from the caller would leak file-type-specific logic into code that shouldn't care |

## How it works — extracting Sarah's document

1. `Employee_Leave_Policy.pdf` (3 pages) arrives from Sprint 2's upload.
2. `ParserService.parse()` sees the `.pdf` extension and calls
   `parse_pdf()`.
3. PyMuPDF opens the file and iterates all 3 pages, concatenating their
   text into one string.
4. The result looks like:
   `"Welcome to Acme Corp... Section 2: Leave Policy. All full-time
   employees are entitled to 12 paid sick leaves per calendar year,
   accrued monthly at 1 leave per month... Section 3: Benefits..."`

This single string — with the sick-leave sentence now sitting inside it as
plain text — is exactly what Sprint 4's chunker receives next.

## One deliberate scope boundary worth knowing

`page.get_text()` concatenates every page into one string with no marker
for where page 1 ends and page 2 begins. This is a scope choice, not an
oversight: the parser's only job is turning binary → plain text. Anything
that needs page numbers (like citing "this came from page 2") would need
to be built on top of this, tracking boundaries explicitly — the frontend
(Sprint 13) deliberately shows filename + relevance instead of a page
number, rather than inventing one.
