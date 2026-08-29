# Frontend Sprint — Next.js UI

## The example at this step

Everything through Sprint 12 was API-only, testable via Swagger or curl.
This sprint gives Sarah an actual browser page: somewhere to upload
`Employee_Leave_Policy.pdf`, watch it process, and type *"How many sick
leaves do I get per year?"* into a chat box.

## Why the scope matches what the backend can actually do

Before writing any UI code, the backend was checked feature-by-feature,
and the UI was scoped to match reality rather than build screens for
features that don't exist yet:

| Feature | Why it wasn't built |
|---|---|
| Chat streaming | `POST /chat` (Sprint 8/9) is a single blocking response — there's no SSE or WebSocket endpoint to stream from |
| Chat history list | Conversation storage (Sprint 9) is in-memory only, with no endpoint to list past conversations |
| Collections / knowledge-bases | No such grouping exists anywhere in the document schema |
| Dashboard analytics | No aggregation endpoints exist on the backend |
| Forgot/reset password | Only register/login/me exist in `app/auth/router.py` |

Building UI for any of these would mean either an empty "coming soon"
shell or, worse, silently fabricated data — the scope was matched to what
the backend genuinely supports instead.

## What we built

**Stack:** Next.js 16 (App Router, Turbopack), TypeScript, Tailwind v4,
shadcn/ui (Base UI primitives), TanStack Query, React Hook Form + Zod.

```
frontend/
├── types/           # mirror the real Pydantic schemas, field-for-field
├── lib/api/          # one centralized fetch client, one module per domain
├── lib/auth/          # session restoration, login/register/logout
├── hooks/             # TanStack Query hooks (polling, mutations)
└── app/(auth)/, app/(dashboard)/   # route groups
```

**Pages:** Login, Register, Chat, Documents, Search, Settings.

## Classes & libraries used, and why

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| **TanStack Query** | Fetches and caches API data, and re-polls it on an interval | Powers the Documents page: after Sarah uploads her PDF, the page polls `GET /documents/14` every few seconds until `status` flips from `"pending"` to `"completed"`, without a manual refresh | Fetching once with plain `fetch()` on page load would show Sarah a stale "Processing..." forever unless she reloads the page herself |
| `hooks/use-document-filename.ts` | Joins a chat answer's source reference back to the real document list to show the real filename | Chunk metadata (Sprint 4) stores the on-disk UUID storage name, not the name Sarah gave the file — this hook cross-references `document_id` against the documents list (which does have the real name, from Postgres, Sprint 10) | Displaying the raw metadata filename directly would show Sarah a meaningless UUID like `a36ae1fc-...pdf` instead of `Employee_Leave_Policy.pdf` |
| **Base UI** (via shadcn/ui, not Radix) | The underlying primitive library behind every dropdown, dialog, and menu component | shadcn/ui's generator produced components built on this; its composition API uses a `render` prop instead of Radix's more commonly documented `asChild` | Once discovered, every trigger-wrapping component was written consistently against Base UI's actual API rather than assuming Radix conventions from other tutorials |
| `output: "export"` (Next.js static export) | Builds the frontend as plain static HTML/CSS/JS with no Node server required | This app has zero server-only features — no API routes, no server actions, no `next/image`, no dynamic route params — confirmed by checking for all of them before choosing this | A standard Next.js server deployment would need a running Node process purely to serve pages that don't actually need server-side rendering, at real ongoing hosting cost |
| `AnswerQualityBadge` (`components/chat/answer-quality-badge.tsx`) | Renders the backend's `search_evaluation.quality` label (`Excellent`/`Good`/`Weak`) as a colored badge next to each answer, with the match percentage | The backend (Sprint 9's `SearchEvaluator`) had graded every answer's source match since it was built, but no UI ever showed it to Sarah — added after live testing showed there was no way to tell a strong answer from a borderline one at a glance | Showing the raw `best_score` number (e.g. `0.765`) would mean nothing to Sarah without context; the color-coded label with a percentage reads instantly |

## How it works — Sarah's session, end to end

1. Sarah registers and logs in (Sprint 10's JWT flow) — the token is
   stored and attached to every subsequent API call by `lib/api/`.
2. She uploads `Employee_Leave_Policy.pdf` on the Documents page. The page
   shows `status: "pending"`, then polls until the worker (Sprint 12)
   finishes and it flips to `"completed"`.
3. She opens the Chat page and types *"How many sick leaves do I get per
   year?"*
4. The request goes to `POST /chat`, and the full RAG pipeline (Sprints
   6–9) runs; the answer *"You are entitled to 12 paid sick leaves per
   year, accrued at 1 per month"* comes back along with its source.
5. The chat UI renders the answer and, underneath it, *"Answered using:
   Employee_Leave_Policy.pdf"* with a relevance score — computed with the
   same `1 / (1 + distance)` formula the backend itself uses (Sprint 9),
   reused rather than reinvented, so the number Sarah sees matches what
   the backend actually calculated. Right next to the answer,
   `AnswerQualityBadge` shows **"✓ Excellent match · 78%"** in green,
   reading `search_evaluation.quality` and `.best_score` straight from the
   same `/chat` response — verified live during testing with this exact
   question and document.
6. If Sarah had instead asked something the document doesn't cover, the
   hallucination guard's *"I don't have enough information"* response
   (Sprint 9) renders the same way any other answer does — the UI doesn't
   need special-case logic for it.

## Deploying the frontend separately from the backend

Because the frontend needs no server, it's deployed as a free static site
— entirely separate from the web/worker/database services in Sprint 12.
This was a deliberate design goal from the start: the frontend can be
changed, redeployed, or removed entirely without touching the API or its
business logic, and vice versa.
