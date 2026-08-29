# Sprint 2 — Document Upload

## The example at this step

Sarah selects `Employee_Leave_Policy.pdf` on her computer and clicks
upload. This file explains what happens to that file the moment it reaches
the server, before any parsing or AI is involved at all.

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

**File:** `app/api/upload.py` — checks the file extension against an
allowlist (`.pdf`, `.docx`, `.txt`) before accepting the upload at all.

## Classes & libraries used, and why

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `StorageService.save_file()` | Renames every uploaded file to a random UUID before saving it | If two different employees at Acme Corp both upload a file named `policy.pdf`, storing by original name would let the second upload silently overwrite the first — a real data-loss and cross-user leak risk | Keeping the original filename is simpler, but only works safely if you can guarantee no two users ever pick the same filename, which you can't |
| Extension **allowlist** (`{".pdf", ".docx", ".txt"}`) in `app/api/upload.py` | Rejects any file type not explicitly expected | Anything not on the list is refused by default — the safer posture | A **blocklist** of dangerous extensions (`.exe`, `.sh`, …) only stops the dangerous types you thought to list; an allowlist doesn't need to know about threats in advance |
| `UploadFile` (FastAPI/Starlette) | Streams the incoming file to disk instead of loading it fully into memory first | Handles Sarah's PDF (or a much larger one) without holding the whole thing in RAM before it's even validated | Reading `await file.read()` into a single bytes object works for small files but risks memory pressure on larger uploads |

## How it works — Sarah's PDF, step by step

1. Sarah selects `Employee_Leave_Policy.pdf` in the browser.
2. The frontend sends it as `multipart/form-data` to `POST /upload`.
3. The backend checks the extension is in `{".pdf", ".docx", ".txt"}` →
   `.pdf` passes.
4. `StorageService.save_file()` generates a new name, e.g.
   `f47ac10b-58cc-4372-a567-0e02b2c3d479.pdf`, and writes the file into
   `uploads/` (a Docker volume in production, see Sprint 11).
5. The *original* name Sarah gave it (`Employee_Leave_Policy.pdf`) is kept
   separately, in Postgres, against her user account (Sprint 10) — the
   UUID is only ever the name of the file *on disk*.
6. The saved path is handed to the parser (Sprint 3) as the next step.

Keeping the original filename in Postgres, and only using the UUID for the
file on disk, is what lets the chat UI later show Sarah "Answered using:
**Employee_Leave_Policy.pdf**" instead of a meaningless UUID string.
