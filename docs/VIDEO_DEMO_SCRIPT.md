# Video Demo Script — Explaining This RAG Chatbot to Students

A narration-ready walkthrough for demonstrating this application on
screen. Unlike the rest of `docs/` (written as a technical reference),
this file is written to be *spoken* — one running example, plain
language, and an explicit "why" for every design decision worth pausing
on. For the code-level detail behind any claim here, see
[`RAG_PIPELINE.md`](RAG_PIPELINE.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md).

**The one example used throughout:** upload `leave_policy.pdf`,
containing the sentence *"Employees receive 30 days of annual leave after
completing one year of service."* Then ask: *"How many annual leave days
do employees receive?"*

**The opening line to camera:**

> "I built a chatbot that answers questions about your own documents —
> not from the internet, from the actual file you upload. Let me show you
> exactly what happens, end to end."

---

## Part 1 — Uploading the Document

**On screen:** log in, go to the Documents page, upload `leave_policy.pdf`.
The UI shows `status: pending`, then a few seconds later flips to
`completed`.

**Narration, in order:**

### 1. The file is saved under a random name, not its real name

*Why:* if two different users both upload a file called `policy.pdf`,
and the server saved it by its original name, the second upload would
silently overwrite the first person's file. So the server renames it to
something like `a1b2c3d4-....pdf` on disk, and remembers the real name
(`leave_policy.pdf`) separately in the database — that's what's shown
back to the user everywhere in the UI.

### 2. The upload request returns instantly — it doesn't wait for processing

*Why:* if the browser had to sit and wait while the server parses a PDF,
splits it into pieces, and generates embeddings for a 200-page document,
that request could take 30–40 seconds or time out entirely. Instead, the
API just saves the file, marks it `"pending"` in the database, and
responds immediately. A **separate background process** does the actual
heavy work.

### 3. Why the worker checks every 5 seconds

There's a separate program (`app/worker.py`) running in its own process,
whose only job is: *every 5 seconds, ask the database "is there anything
waiting to be processed?"* If yes, pick up to 5 documents and process
them.

- It's the simplest possible way to hand work off between two separate
  processes — no message queue, no extra infrastructure to run, just
  "check the database periodically."
- 5 seconds is a deliberate middle ground: check too often (every 100ms)
  and the database gets hammered with mostly-empty queries for no
  benefit; check too rarely (every 60 seconds) and a user who just
  uploaded a document sits there wondering why nothing's happening. 5
  seconds means "feels responsive" without being wasteful.
- **Honest trade-off worth saying out loud:** this is a good, simple
  starting point, not what a large-scale system would use. At real scale
  this polling loop would become a message queue (the worker gets *told*
  immediately instead of asking repeatedly) — a deliberate simplification
  made for this project's size, not something hidden. See
  [`PRODUCTION_EVOLUTION.md`](PRODUCTION_EVOLUTION.md).

### 4. What the worker actually does — the part worth slowing down for

- **Parse:** turn the PDF's binary bytes into plain text —
  *"Employees receive 30 days of annual leave after completing one year
  of service."*
- **Chunk:** split the text into ~1000-character pieces, with 200
  characters of overlap between them.
  *Why chunk at all:* the AI model that turns text into a "meaning
  vector" (next step) works best on a focused piece of text, not a whole
  document — and later, the LLM can only read a limited amount of text at
  once, so the entire document can't be handed over every time.
  *Why overlap:* if a sentence happens to fall right on a chunk boundary,
  overlap means the next chunk still has the tail end of that sentence,
  so "30 days of annual leave" never gets accidentally split in half.
- **Embed:** turn the chunk into a list of 384 numbers using a small AI
  model (`all-MiniLM-L6-v2`) — the "meaning fingerprint" of that text. Two
  pieces of text with similar meaning end up with numbers that are close
  together, even if they use completely different words.
  *Why this specific, smaller model instead of a bigger, more accurate
  one:* it runs on an ordinary CPU, no GPU or paid API required — a
  deliberate choice to keep this runnable on modest infrastructure, with
  the honest trade-off that a larger model would be somewhat more
  accurate.
- **Store:** save that vector into a vector database (ChromaDB) *and*
  separately index the same chunk's raw text into a keyword search index
  (BM25) — two different search systems, on purpose (explained next).

---

## Part 2 — Asking the Question

**On screen:** type *"How many annual leave days do employees receive?"*
into the chat box, and narrate what's happening before the answer even
starts appearing.

### 1. A quick check: are you trying to look at someone else's documents?

If the question literally mentions another user (like "what does user
3's document say"), it's blocked before any search happens. This is a
narrow, specific guard — the *real* protection is structural: every
search is already scoped to only the requesting user's own uploaded
documents by the database, this check just catches an obvious attempt on
top of that.

### 2. The question gets rewritten twice by the AI, before anything is searched

- First, it's turned into a clean, standalone question (useful mid-
  conversation — if the next message is "and how do I request it?" the
  system needs to know "it" means annual leave).
- Then, it's expanded into 3 different phrasings of the same question —
  because the exact words someone types might not match the document's
  exact wording, so trying a few variations increases the chance of a
  good match.

*Good "aha" moment for students:* the system doesn't just search for the
literal words typed — it actively tries to understand and rephrase the
question first.

### 3. Hybrid search — the most important concept to slow down for

The system searches **two completely different ways at the same time**,
then combines the results:

- **Meaning-based search (vector search):** finds chunks whose "meaning
  fingerprint" is close to the question's fingerprint. This would still
  work even for *"How much yearly vacation do staff get?"* — different
  words, same meaning.
- **Keyword search (BM25):** finds chunks that literally contain the
  words in the question. This is what catches exact terms — product
  codes, IDs, specific names — that meaning-based search can sometimes
  rank lower than it should.

The two sets of results are combined with a weighted formula (60% weight
to the meaning-based score, 40% to the keyword score), and anything with
too low a combined score is thrown out entirely rather than forced into
the results.

*Why do both instead of just one:* each has a real blind spot on its own.
Meaning-search alone can miss exact terms; keyword-search alone can't
understand a paraphrased question. Doing both and combining them covers
more real questions correctly.

### 4. A second AI pass double-checks the results for quality (reranking)

The first search is fast but a little rough — it scores each chunk
against the question independently. A second, slower, more careful model
reads the question *and* each candidate chunk *together* and re-scores
them — genuinely more accurate, just too slow to run on everything, so it
only runs on the shortlist the first search already narrowed down.
Anything that still scores too low here gets dropped too — so if only one
chunk is actually relevant, that's what the system uses, not a
padded-out "top 3 regardless of quality."

### 5. The retrieved chunk is handed to the LLM with explicit rules, not just dumped in

The prompt sent to the AI explicitly says: *"Answer only using this
context. If it's not here, say you don't have enough information. Don't
make anything up."* This is the actual mechanism that keeps answers
grounded in the real document instead of the AI's general
internet-trained knowledge.

### 6. Before the user sees the answer, a second AI call fact-checks the first one

Worth genuinely pausing on — a real, separate step, not just a prompt
trick:

- The AI generates an answer.
- A *second*, independent AI call is asked: "does this answer actually
  match what's in the retrieved text, or is it making something up?"
- If that check fails, the system throws the answer away and generates a
  new one with even stricter instructions.

*Why this matters:* this is the system's real defense against
hallucination — an AI confidently stating something false. Instead of
just hoping the first answer is accurate, it's actually verified before
the user ever sees it.

### 7. The answer appears word by word — be honest about what this is and isn't

It *looks* like the AI is typing live, but it isn't — the entire answer,
already generated and already fact-checked (steps 5–6), is revealed
progressively for a better feel, rather than popping onto the screen all
at once. Worth being upfront about in a teaching video: it's a UX
choice, not real live generation, and it slightly *increases* total wait
time rather than reducing it — the trade-off made was "keep the
fact-checking step intact" over "show the very first raw token as fast
as possible."

### 8. The final answer shows where it came from

Underneath the answer, the UI shows the source document and a relevance
percentage, computed from that same reranking score. This lets a student
(or any user) actually verify the claim against the real document instead
of just trusting the AI.

---

## Suggested Video Structure

1. **Hook (30s):** "Here's a chatbot that only answers from documents
   *you* give it — let me show you exactly what happens under the hood."
2. **Upload demo (2–3 min):** Part 1 above, pausing on chunking +
   embeddings with a visual (a document breaking into pieces, then
   pieces turning into rows of numbers).
3. **Question demo (3–4 min):** Part 2 above, pausing hardest on hybrid
   search and the hallucination check — these are the two ideas that
   make this more than a toy project.
4. **Honest limitations (1 min):** polling instead of a queue, no real
   token streaming, one BM25 index rebuilt from scratch each time, no
   evaluation benchmark yet — this is what separates a genuine teaching
   demo from a sales pitch, and it's exactly what's in
   [`PRODUCTION_EVOLUTION.md`](PRODUCTION_EVOLUTION.md).
5. **Close:** point students at the repo's `docs/` folder for the
   code-level detail behind everything just shown — start with
   [`RAG_PIPELINE.md`](RAG_PIPELINE.md).
