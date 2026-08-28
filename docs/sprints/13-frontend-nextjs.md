# Frontend Sprint — Next.js UI

## Objective

Everything through Sprint 12 was API-only, tested via Swagger and curl.
This sprint built an actual browser UI — deliberately scoped down from a
much larger initial spec, based on a real audit of what the backend could
actually support.

## Why the scope was cut down from the original request

The initial ask described a large, enterprise-style platform (chat
streaming, chat history sidebar, collections/knowledge-bases, dashboard
analytics, forgot-password). Before writing any UI code, the actual backend
was audited feature-by-feature, and the scope was **deliberately reduced**,
documented in `frontend/docs/API-INTEGRATION.md`:

| Cut feature | Real reason (verified in backend code) |
|---|---|
| Chat streaming | `POST /chat` is a single blocking response (Sprint 8/9) — no SSE, no WebSocket exists |
| Chat history list | Conversation store is in-memory only (Sprint 9) — no listing endpoint, no persistence |
| Collections/knowledge-bases | No grouping concept anywhere in the document schema |
| Dashboard stats/analytics | No aggregation endpoints exist |
| Forgot/reset password | Not in `app/auth/router.py` — only register/login/me exist |

This is a deliberate example of **not building fake functionality** —
rather than ship UI for features the backend can't actually support (either
as empty "coming soon" shells, or worse, silently faking data), the scope
was matched to reality.

## What we built

**Stack:** Next.js 16 (App Router, Turbopack), TypeScript, Tailwind v4,
shadcn/ui (built on **Base UI** primitives, not Radix — a real, non-obvious
distinction, see below), TanStack Query, React Hook Form + Zod.

**Structure:**
```
frontend/
├── types/           # mirror the real Pydantic schemas, field-for-field
├── lib/api/          # one centralized fetch client, one module per domain
├── lib/auth/          # session restoration, login/register/logout
├── hooks/             # TanStack Query hooks (polling, mutations)
└── app/(auth)/, app/(dashboard)/   # route groups
```

**Pages:** Login, Register, Chat, Documents, Search, Settings — exactly
matching what the backend genuinely supports.

## Real bugs found and fixed while building this (not hypothetical)

### 1. Backend data shown incorrectly (two separate instances)

`SourceReference.filename` and `SearchResult.metadata.filename` both
return the **on-disk UUID storage name** (Sprint 2's renamed file), not the
original upload name — because chunk metadata (Sprint 4) was tagged with
`location.name` (the storage path), never the original filename. Fixed by
cross-referencing `document_id` against the already-fetched documents list
(which *does* have the real filename, from Postgres, Sprint 10) —
`hooks/use-document-filename.ts` — joining two real API responses, not
inventing data.

### 2. A relevance score that would have been actively misleading

An early version of the search UI displayed `score * 100 + "%"` directly.
Verified by reading `app/services/search.py`: `score` is a **raw Chroma L2
distance** — lower is better, unbounded — not a 0-100% similarity. Fixed
using the exact same `1 / (1 + distance)` formula the backend's own
`hybrid_search.py` already established (Sprint 9), rather than inventing a
different conversion.

### 3. Base UI vs Radix — a real library-version surprise

The installed `shadcn/ui` generator produced components built on **Base
UI**, not the more commonly-documented Radix primitives. This meant the
well-known `asChild` prop pattern **doesn't exist** — Base UI uses a
`render` prop instead. Discovered via a real TypeScript error, confirmed
by reading the actual generated component source and Base UI's own
composition docs before fixing every trigger-wrapping component
consistently.

### 4. A genuine runtime crash: `MenuGroupContext is missing`

`DropdownMenuLabel` was used directly inside `DropdownMenuContent` with no
`DropdownMenuGroup` wrapper. Base UI's `Menu.GroupLabel` (unlike Radix's
more lenient label) *strictly requires* a `Menu.Group` ancestor. This
shipped initially, was caught by the user reporting the actual runtime
error, then fixed and verified live (registered a user, opened the menu,
confirmed no crash).

### 5. Mobile drawer not closing on navigation

The nav `Link`'s `onClick` handler for closing the mobile drawer was
unreliable — raced against Next's own client-side navigation. Fixed by
reacting to `usePathname()` changing instead (a `useEffect` that closes the
drawer whenever the route actually changes) — a more robust signal than a
click-event handler.

## Deployment — a real architecture realization

The app has **zero server-only features** (no API routes, no server
actions, no `next/image`, no dynamic route params) — confirmed by grepping
for all of them before making this decision. This means it doesn't need a
running Node server at all: `output: "export"` in `next.config.ts` produces
a plain static site, deployable for free (no paid Render web-service
compute needed for the frontend at all).

**A real bug caught during this exact verification, not just assumed to
work:** the first local rebuild baked in `http://localhost:8000` instead
of the intended production URL, because `.env.local` (used for local `npm
run dev`) takes precedence over `.env.production` in Next.js's env-loading
order. Confirmed this was a *local-testing-only* artifact — `.env.local`
is gitignored and won't exist on a clean deployment checkout — by
temporarily removing it and rebuilding, which correctly produced the
production URL.

## Positive scenarios

- **Verified live, end to end, against the real running backend
  (Docker Compose, real Postgres/Chroma/BM25/Gemini):** register → auto-
  login → session restore → upload → worker processes it → status updates
  live in the UI → real multi-turn Gemini chat with correct sources → real
  semantic search → delete. Every one of these was directly observed
  working, not assumed from code review alone.
- The hallucination guard's correct "I don't have enough information"
  behavior (Sprint 9) was directly visible and correctly rendered in the
  chat UI during real testing.

## Negative scenarios / limitations

- **No automated frontend test suite** (Vitest/Playwright) — the extensive
  live browser-based verification substituted for it in this build pass;
  genuine follow-up work, not silently skipped.
- No page-number citations (inherited limitation from Sprint 3's parsing —
  the data doesn't exist to show).
- No chat history, collections, or analytics (deliberately, per the scope
  cut above).
- Real-time polling for document status uses TanStack Query's default
  `refetchIntervalInBackground: false` — a background/inactive browser tab
  correctly pauses polling (standard, sensible behavior, verified during
  testing when an automated test tab's `visibilityState` was `"hidden"`),
  meaning a user who uploads a document and switches away from the tab
  won't see the status update until they return to it.
