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

| Feature | Why it wasn't built (at the time) |
|---|---|
| Chat history list | Conversation storage (Sprint 9) is in-memory only, with no endpoint to list past conversations |
| Collections / knowledge-bases | No such grouping exists anywhere in the document schema |
| Dashboard analytics | No aggregation endpoints exist on the backend |
| Forgot/reset password | Only register/login/me exist in `app/auth/router.py` |

Building UI for any of these would mean either an empty "coming soon"
shell or, worse, silently fabricated data — the scope was matched to what
the backend genuinely supports instead.

Chat streaming was in this table too, originally — `POST /chat` was a
single blocking response with nothing to stream from. It was revisited
later once the backend grew a `POST /chat/stream` endpoint (Sprint 9);
see below for what actually got built and why it's not real token-level
LLM streaming.

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
| `llmProviderStorage` (`lib/llm-provider.ts`) + `useLlmProvider` hook | Reads/writes Sarah's Ollama-vs-Gemini choice in `localStorage`, and a Settings page card to change it | Sprint 8's `/chat` endpoint accepts a per-request `llm_provider` field, but something has to decide what to send — this is the UI for that decision, saved the same way the auth token already is | A dropdown re-fetched from the server on every page load would need a new API call and a place to store the preference server-side; `localStorage` is enough for a per-browser convenience like this one |
| `apiClient.stream()` (`lib/api/client.ts`) | Reads `POST /chat/stream`'s Server-Sent Events using plain `fetch()` + `response.body.getReader()`, parsing each `data: ...` frame as it arrives | The browser's built-in `EventSource` only supports GET requests with no custom headers — this app authenticates every request with an `Authorization: Bearer <token>` header, which `EventSource` has no way to send | Switching the whole app to cookie-based auth just to use `EventSource` would be a much bigger change for one endpoint; a small hand-rolled SSE reader on top of the same `fetch()` client already used everywhere else was the smaller, more consistent option |
| `useChat`'s streaming state | Pushes an empty assistant message onto state immediately, then appends each incoming word to that message's `content` as chunks arrive, instead of one `setState` after an `await` | This is what actually makes the answer appear progressively — the network layer alone doesn't do this; something has to turn "a stream of chunks" into "a message that grows" | The alternative — buffer every chunk and set state once at the end — would defeat the entire point of streaming, back to a single pop-in |
| Blinking cursor (`chat-message.tsx`) | A small `animate-pulse` block rendered after the answer text while `message.isStreaming` is true | Gives Sarah a visual cue that more text is still coming, the same convention most chat UIs use | Without it, a short pause between words could look like the answer had already finished |

**Settings page — AI Model card:** two buttons, Ollama (default,
highlighted) and Gemini, styled identically to the existing Appearance
card. Selecting one writes it to `localStorage`; `useChat`'s
`sendMessage()` reads it fresh on every send, so Sarah can switch
mid-conversation without reloading the page.

## How it works — Sarah's session, end to end

1. Sarah registers and logs in (Sprint 10's JWT flow) — the token is
   stored and attached to every subsequent API call by `lib/api/`.
2. She uploads `Employee_Leave_Policy.pdf` on the Documents page. The page
   shows `status: "pending"`, then polls until the worker (Sprint 12)
   finishes and it flips to `"completed"`.
3. She opens the Chat page and types *"How many sick leaves do I get per
   year?"*
4. The request goes to `POST /chat/stream`, and the full RAG pipeline
   (Sprints 6–9) — including the hallucination guard — runs to completion
   exactly as it would for `POST /chat`. Once it's done deciding the final
   answer is *"You are entitled to 12 paid sick leaves per year, accrued
   at 1 per month,"* the chat UI reveals it to Sarah a word at a time
   instead of popping in all at once, with a blinking cursor after the
   last revealed word.
5. Once the reveal finishes, the chat UI shows, underneath the answer, *"Answered using:
   Employee_Leave_Policy.pdf"* with a relevance score — computed with the
   same `1 / (1 + distance)` formula the backend itself uses (Sprint 9),
   reused rather than reinvented, so the number Sarah sees matches what
   the backend actually calculated. Right next to the answer,
   `AnswerQualityBadge` shows **"✓ Excellent match · 78%"** in green,
   reading `search_evaluation.quality` and `.best_score` straight from the
   stream's final `"done"` event — verified live during testing, watching
   the answer render progressively before the badge and sources appeared.
6. If Sarah had instead asked something the document doesn't cover, the
   hallucination guard's *"I don't have enough information"* response
   (Sprint 9) renders the same way any other answer does — the UI doesn't
   need special-case logic for it.
7. If Sarah opens Settings and switches **AI Model** to Gemini first, her
   next question is answered by `gemini-3.6-flash` instead of the local
   Ollama model — no reload needed, the choice is read fresh from
   `localStorage` on send. If the server has no Gemini API key configured,
   the same error-bubble UI that already exists for network failures
   shows the backend's exact message instead — no special-case error
   handling needed for this either.

## Deploying the frontend separately from the backend

Because the frontend needs no server, it's deployed as a free static site
— entirely separate from the web/worker/database services in Sprint 12.
This was a deliberate design goal from the start: the frontend can be
changed, redeployed, or removed entirely without touching the API or its
business logic, and vice versa.
