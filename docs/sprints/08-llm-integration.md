# Sprint 8 — LLM Integration

## The example at this step

Retrieval (Sprint 7) found chunk `"14-1"` — the raw text *"All full-time
employees are entitled to 12 paid sick leaves per calendar year, accrued
monthly at 1 leave per month."* That's still just a paragraph, not an
answer to Sarah's question. This step uses an LLM to turn "here's the
question, here's the relevant paragraph" into a real sentence: *"You are
entitled to 12 paid sick leaves per year, accrued at 1 per month."*

## What we built

**File:** `app/services/llm/base.py` — an abstract interface every
provider implements:
```python
class LLMService(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass
```

**File:** `app/services/llm/gemini.py`:
```python
class GeminiService(LLMService):
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)  # gemini-3.6-flash

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text
```

**File:** `app/services/llm/ollama.py` — same interface, backed by a
locally-running Ollama daemon instead of a cloud API.

## Classes & libraries used, and why

| Class / library | What it does | Why we used it | How it compares to the alternative |
|---|---|---|---|
| `LLMService` (abstract base class) | Defines one method, `generate(prompt) -> str`, that every provider must implement | The rest of the pipeline (`RAGChatService`, Sprint 9) calls `AIServiceRegistry.get_llm().generate(prompt)` and has no idea whether that's Gemini or Ollama underneath — this is the Strategy design pattern | Calling `genai.GenerativeModel(...)` directly from inside the chat logic would mean switching providers later requires editing the chat logic itself, not just a config value |
| `GeminiService` | Sends the prompt (Sarah's question + the sick-leave paragraph) to Google's `gemini-3.6-flash` model over the network, returns the generated text | Cloud-hosted, no local hardware needed, strong general-purpose quality for turning retrieved facts into a natural sentence | Ollama (below) is the deliberate lower-cost, local alternative — the choice between them is a real config value, not a hardcoded decision |
| `OllamaService` | Same interface, but talks to a locally-running Ollama daemon (e.g. running `llama3.1`) instead of a cloud API | No per-call API cost, useful for local development | Requires a reachable Ollama daemon — this only works where one exists on the same machine/network, which a cloud host like Render doesn't have, so Gemini is the only viable option there |
| `AIServiceRegistry.get_llm(provider=None)` | Returns the matching, already-initialized `LLMService` — `provider` if given, otherwise falls back to `settings.llm_provider` | Caches Gemini and Ollama as two separate singletons (a small `dict`, not one slot), so a single running server can serve some requests with Ollama and others with Gemini without re-initializing either client each time | An earlier version cached only one instance for the whole process, tied to a single `.env` value — switching required restarting the server. Caching per-provider is what makes a *per-request* choice possible at all |

## How it works — answering Sarah's question

1. `RAGChatService` (Sprint 9) builds one prompt combining Sarah's
   question and the retrieved sick-leave paragraph — something like:
   *"Using only the following context, answer the question. Context: 'All
   full-time employees are entitled to 12 paid sick leaves...' Question:
   'How many sick leaves do I get per year?'"*
2. It calls `AIServiceRegistry.get_llm(llm_provider).generate(prompt)`,
   where `llm_provider` came from the `/chat` request body.
3. If Sarah left the default in place, that's Ollama (`llama3.1`,
   running locally); if she switched to Gemini in Settings first, the
   prompt goes to Google's Gemini API (`gemini-3.6-flash`) instead. Either
   way the generated answer comes back the same shape — e.g. *"You are
   entitled to 12 paid sick leaves per year, accrued at 1 per month."*
4. That text is what gets returned to Sarah's browser, alongside the
   source chunk it came from (Sprint 9's `SourceBuilder`).

## Why an abstract base class instead of calling Gemini directly

The concrete benefit shows up the moment you need a second provider:
swapping providers required **zero changes** to `RAGChatService` — the
code that actually orchestrates the whole chat flow. It just calls the
interface method. This project genuinely runs with either Gemini or
Ollama, and — since the frontend feature below — **per question, not just
per server** — with no changes anywhere else in the pipeline.

## Letting Sarah choose, instead of fixing it in `.env`

Originally `LLM_PROVIDER` was a single value in `.env`, decided once when
the server starts and applying to every user's every question. That's
fine for a server with one intended provider, but doesn't let *Sarah*
decide anything — a real limitation once Gemini was also available and
working.

**File:** `app/api/chat.py` — `ChatRequest` gained an optional field:
```python
llm_provider: Literal["ollama", "gemini"] | None = None
```
Left out (or `null`), it falls back to the server's `.env` default — so
nothing breaks for a caller that doesn't know about this field. Set to
`"gemini"` or `"ollama"`, it overrides the default for that one request
only.

**File:** `frontend/app/(dashboard)/settings/page.tsx` — an **AI Model**
card next to Appearance, with two buttons: Ollama (highlighted by
default) and Gemini. The choice is saved in the browser's `localStorage`
(`frontend/lib/llm-provider.ts`) — a per-browser convenience, the same way
the auth token and theme already work — and `frontend/hooks/use-chat.ts`
reads it and includes it on every `POST /chat` call.

If Sarah switches to Gemini but the server has no `GEMINI_API_KEY`
configured, `AIServiceRegistry.get_llm()` raises a clear error
(*"Gemini is not configured on this server..."*) which `POST /chat`
turns into an HTTP 400 — Sarah sees that exact sentence in the chat
window instead of a stack trace or a silently wrong answer.

## When Gemini itself fails — quota limits, not just misconfiguration

A configured Gemini key can still fail *while answering* — most commonly
by hitting a quota. Google's free tier caps `gemini-3.6-flash` at **20
requests per day**, and a single chat message can make up to five Gemini
calls (query enhancement, query expansion, generate, hallucination-guard
validate, and — before the fix in Sprint 9 — an almost-always-triggered
regenerate), so that cap is easy to hit in only a handful of real
questions.

Before this was handled, an exhausted quota surfaced as a raw, unhandled
`500` after Google's own client had already spent up to two minutes
silently retrying with backoff. **File:** `app/api/chat.py` now wraps the
call to `service.chat()`:

```python
try:
    return await service.chat(...)
except GoogleAPIError as error:
    raise HTTPException(status_code=503, detail=f"Gemini API error: {error.message}")
```

This catch is deliberately narrow — only `google.api_core.exceptions.GoogleAPIError`
(quota limits, auth failures, other Gemini-side errors) is translated into
a clean message. Anything else (a bug in retrieval, a database error) is
left alone and still surfaces as a normal `500`, so this doesn't hide
unrelated problems behind a misleading "Gemini" label. Verified live: a
quota-exhausted request now returns `503` with Google's own message
(*"Quota exceeded for metric: ... limit: 20, model: gemini-3.6-flash"*)
in ~30 seconds, instead of crashing after ~145 seconds.
