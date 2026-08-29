# Complete Sprint-by-Sprint Documentation

A clear technical walkthrough of this RAG chatbot's development — what was
built, **why that specific class or library was chosen**, what it actually
does, and how it compares to the obvious alternatives. Written after
completing the full application (backend + frontend + deployment), based on
a direct re-read of the real code.

## The one example used in every file

To keep the explanation concrete instead of abstract, every file in this
folder traces **the same real scenario** end to end:

> **Sarah**, an employee at **Acme Corp**, uploads a file called
> `Employee_Leave_Policy.pdf`. Page 2 of that file says:
> *"All full-time employees are entitled to 12 paid sick leaves per
> calendar year, accrued monthly at 1 leave per month."*
> Later, Sarah opens the chatbot and asks:
> **"How many sick leaves do I get per year?"**
> The system correctly answers: *"You are entitled to 12 paid sick leaves
> per year, accrued at 1 per month."*

Each file below picks up this exact example at the point relevant to that
sprint — the same file name, the same sentence, the same question — so you
can follow one request all the way from upload to answer across the whole
documentation set.

## Reading order

| # | File | What it explains, using Sarah's example |
|---|---|---|
| 0 | [00-overview-and-architecture.md](00-overview-and-architecture.md) | The whole system in one diagram, and where each piece sits |
| 1 | [01-project-setup.md](01-project-setup.md) | Why the backend is split into layers, and how Sarah's request moves through them |
| 2 | [02-document-upload.md](02-document-upload.md) | How `Employee_Leave_Policy.pdf` gets safely onto the server |
| 3 | [03-document-parsing.md](03-document-parsing.md) | How the PDF's text is extracted with PyMuPDF |
| 4 | [04-chunking-and-storage.md](04-chunking-and-storage.md) | How the extracted text is split so the sick-leave sentence stays intact |
| 5 | [05-embeddings-and-ai-registry.md](05-embeddings-and-ai-registry.md) | How that chunk becomes a 384-number vector |
| 6 | [06-vector-database-chromadb.md](06-vector-database-chromadb.md) | Where that vector is stored, and how it's found again |
| 7 | [07-semantic-retrieval.md](07-semantic-retrieval.md) | How Sarah's question is matched back to the right chunk |
| 8 | [08-llm-integration.md](08-llm-integration.md) | How Gemini turns the matched chunk into a real sentence |
| 9 | [09-rag-pipeline-and-hybrid-search.md](09-rag-pipeline-and-hybrid-search.md) | How keyword search, reranking, and the hallucination check all combine on this one question |
| 10 | [10-authentication-and-multiuser.md](10-authentication-and-multiuser.md) | Why only Sarah can ever see or query her own document |
| 11 | [11-production-engineering-docker-ci.md](11-production-engineering-docker-ci.md) | How this whole flow runs identically in Docker and is tested in CI |
| 12 | [12-deployment-and-worker-queue.md](12-deployment-and-worker-queue.md) | How Sarah's upload is processed in the background, in production |
| 13 | [13-frontend-nextjs.md](13-frontend-nextjs.md) | How Sarah actually sees and uses all of this in a browser |
| 14 | [14-bugs-and-lessons-learned.md](14-bugs-and-lessons-learned.md) | Every real bug hit while building this exact flow, and the actual fix |

## How each file is structured

- **The example at this step** — where Sarah's document/question is right
  now in the pipeline
- **What we built** — the real class/file involved
- **Classes & libraries used, and why** — a table: what each one does, the
  concrete benefit of using it, and how it compares to the obvious
  alternative
- **How it works** — Sarah's example walked through this exact step

## The single most important file, if you only read one

[14-bugs-and-lessons-learned.md](14-bugs-and-lessons-learned.md) — the
consolidated list of every real bug found while building this pipeline,
what caused it, and exactly how it was fixed.
