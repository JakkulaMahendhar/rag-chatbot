# Sprint 2 — Document Upload

## Objective

Let a user get a file (PDF/DOCX/TXT) from their computer onto the server,
safely, before any processing (parsing, chunking, etc.) happens.

## What we built

**File:** `app/services/storage.py`

```python
class StorageService:
    @staticmethod
    async def save_file(file: UploadFile):
        extension = Path(file.filename).suffix
        filename = f"{uuid4()}{extension}"          # never trust the original name
        destination = UPLOAD_DIR / filename
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return destination
```

**File:** `app/api/upload.py` — validates file extension against an allowlist
(`.pdf`, `.docx`, `.txt`) *before* accepting the upload.

## Why we did it this way

### Why rename every uploaded file to a UUID?

Real scenario this prevents: two different users both upload a file named
`resume.pdf`. If we stored files by their original name, the second upload
could silently overwrite the first user's file — a real data-loss and
security bug (one user could even read another user's document by
guessing/uploading a same-named file). Renaming to `f"{uuid4()}{extension}"`
makes every stored filename globally unique, regardless of what the user
named their file.

**Real consequence discovered later (see Sprint 9 / bugs doc):** because the
stored filename is a UUID, not the original name, later code that read
`filename` from chunk metadata was showing users a UUID like
`a36ae1fc-236a-4a90-9d7f-6b7cfc693526.txt` instead of their actual
`quarterly-report.pdf` — a real bug we found and fixed in the frontend by
joining back to the database's `filename` column (the *original* name is
stored separately in Postgres, see Sprint 10).

### Why an extension allowlist, not a blocklist?

Blocklisting dangerous extensions (`.exe`, `.sh`, etc.) is a losing game —
you have to know every dangerous extension in advance. Allowlisting
(`{".pdf", ".docx", ".txt"}` in `app/api/upload.py`) means anything not
explicitly expected is rejected by default, which is the safer default.

## How it works — a real walkthrough

1. User selects `employee-handbook.pdf` in the browser.
2. Frontend sends it as `multipart/form-data` to `POST /upload`.
3. Backend checks the extension is in `{".pdf", ".docx", ".txt"}` → passes.
4. `StorageService.save_file()` generates e.g.
   `f47ac10b-58cc-4372-a567-0e02b2c3d479.pdf` and writes the file to
   `uploads/` (a Docker volume in production, see Sprint 11).
5. Returns the saved `Path` object for the next stage (parsing, Sprint 3) to
   use.

## Positive scenarios

- Concurrent uploads from different users never collide (verified: two
  documents named identically by two different users produced two distinct
  UUID-named files with no conflict, during live testing in this project).
- Rejecting unsupported types happens *before* any expensive processing
  (parsing/embedding) is attempted — fails fast, cheaply.

## Negative scenarios / limitations

- **No file size limit was ever explicitly enforced** at this layer. A
  user could upload an extremely large file and the server would still
  attempt to buffer/copy the whole thing. This is a real gap — worth adding
  a max-size check before this goes to genuine production use with
  untrusted users.
- **No virus/malware scanning.** Files are trusted once they pass the
  extension check. Fine for a personal/portfolio project; a real production
  system handling arbitrary user uploads would need this.
- **No duplicate-content detection.** Uploading the exact same PDF twice
  creates two separate documents, two separate sets of chunks/embeddings —
  wasted storage and compute, no dedup logic exists.
