# Sprint 8 — LLM Integration

## Objective

Retrieval (Sprints 6-7) finds relevant text. It doesn't *answer* a question
— it just returns raw chunks. We need a Large Language Model to read the
question plus the retrieved context and generate a coherent natural-
language answer.

## What we built

**File:** `app/services/llm/base.py` — an abstract interface:
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
        self.model = genai.GenerativeModel(settings.gemini_model)  # gemini-2.5-flash

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text
```

**File:** `app/services/llm/ollama.py` — the same interface, backed by a
locally-running Ollama daemon instead of a cloud API.

**File:** `app/core/ai_registry.py`:
```python
@classmethod
def get_llm(cls):
    if cls._llm is None:
        if settings.llm_provider == "gemini":
            cls._llm = GeminiService()
        elif settings.llm_provider == "ollama":
            cls._llm = OllamaService()
    return cls._llm
```

## Why an abstract base class + registry, instead of calling Gemini directly

Real, concrete benefit realized later in this exact project: **swapping
LLM providers required zero changes to `RAGChatService`** (Sprint 9), the
code that actually orchestrates the whole chat flow. It just calls
`AIServiceRegistry.get_llm().generate(prompt)` — it has no idea whether
that's Gemini or Ollama underneath. This is the Strategy design pattern,
and it paid for itself directly: this project genuinely runs with either
provider by changing one config value (`LLM_PROVIDER=gemini` vs
`LLM_PROVIDER=ollama`), verified in both directions during development.

## Why support Ollama at all, given Gemini is the "main" provider

Two real, concrete reasons discovered during this exact project:
1. **Local development without API costs** — Ollama runs entirely on your
   own machine, no per-call cost, no API key needed.
2. **A genuine deployment constraint surfaced later** (Sprint 12): Ollama
   requires a locally-reachable daemon process. On a cloud host like
   Render, there's no "local machine" for Ollama to run on reachable the
   same way — so in production, **Gemini is the only viable option**. This
   is documented explicitly in `render.yaml` as a real deployment
   constraint, not a hypothetical one.

## How it works — a real walkthrough

1. `RAGChatService` (Sprint 9) builds a prompt combining the user's
   question and the retrieved, reranked context chunks.
2. Calls `AIServiceRegistry.get_llm().generate(prompt)`.
3. If `LLM_PROVIDER=gemini`: the prompt is sent to Google's Gemini API
   (`gemini-2.5-flash` model), a real network call, and the generated text
   comes back.
4. The `LLMService` singleton means this provider connection is
   established once per process, not re-initialized on every chat message.

## Positive scenarios

- Verified live, repeatedly, during this project: real questions against
  real uploaded documents produce real, coherent, grounded Gemini-
  generated answers (not mocked/fake responses) — confirmed by inspecting
  actual API responses during development and testing.
- Provider swap genuinely works — both Gemini and Ollama paths were
  exercised during this project's development.

## Negative scenarios / limitations

- **No retry/backoff logic** on the Gemini API call — if the call fails
  (network blip, rate limit, quota exceeded), it fails the whole chat
  request rather than retrying.
- **No streaming support** — `generate()` returns the complete response
  only after Gemini finishes generating it entirely. This was a
  deliberate, documented scope decision for the frontend (Sprint 13): "ship
  with an honest loading state, not fake streaming," rather than silently
  pretending to stream a response that arrives all at once.
- **Cost is not tracked or limited anywhere** — every chat message makes a
  real, billed Gemini API call with no per-user rate limiting on LLM usage
  specifically (there IS a rate limiter on auth endpoints, Sprint 10, but
  not on `/chat`). A malicious or careless user could generate significant
  API cost with no guardrail.
- Switching `LLM_PROVIDER` mid-project (Gemini ↔ Ollama) was observed to
  cause a real, confirmed test failure (`tests/test_settings.py` hardcodes
  an assumption that `llm_provider == "gemini"`) when the actual `.env` was
  set to `ollama` — a small but real example of test/config drift found
  during this project.
