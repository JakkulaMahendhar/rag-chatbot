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
        self.model = genai.GenerativeModel(settings.gemini_model)  # gemini-2.5-flash

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
| `GeminiService` | Sends the prompt (Sarah's question + the sick-leave paragraph) to Google's `gemini-2.5-flash` model over the network, returns the generated text | Cloud-hosted, no local hardware needed, strong general-purpose quality for turning retrieved facts into a natural sentence | Ollama (below) is the deliberate lower-cost, local alternative — the choice between them is a real config value, not a hardcoded decision |
| `OllamaService` | Same interface, but talks to a locally-running Ollama daemon (e.g. running `llama3.1`) instead of a cloud API | No per-call API cost, useful for local development | Requires a reachable Ollama daemon — this only works where one exists on the same machine/network, which a cloud host like Render doesn't have, so Gemini is the only viable option there |
| `AIServiceRegistry.get_llm()` | Reads `LLM_PROVIDER` from settings and returns the matching, already-initialized `LLMService` | The provider connection is set up once per process and reused for every chat message, not re-initialized every time | — |

## How it works — answering Sarah's question

1. `RAGChatService` (Sprint 9) builds one prompt combining Sarah's
   question and the retrieved sick-leave paragraph — something like:
   *"Using only the following context, answer the question. Context: 'All
   full-time employees are entitled to 12 paid sick leaves...' Question:
   'How many sick leaves do I get per year?'"*
2. It calls `AIServiceRegistry.get_llm().generate(prompt)`.
3. With `LLM_PROVIDER=gemini`, that prompt goes to Google's Gemini API
   (`gemini-2.5-flash`), and the generated answer comes back — e.g. *"You
   are entitled to 12 paid sick leaves per year, accrued at 1 per month."*
4. That text is what gets returned to Sarah's browser, alongside the
   source chunk it came from (Sprint 9's `SourceBuilder`).

## Why an abstract base class instead of calling Gemini directly

The concrete benefit shows up the moment you need a second provider:
swapping providers required **zero changes** to `RAGChatService` — the
code that actually orchestrates the whole chat flow. It just calls the
interface method. This project genuinely runs with either Gemini or Ollama
by changing one setting (`LLM_PROVIDER=gemini` vs `LLM_PROVIDER=ollama`),
with no changes anywhere else in the pipeline.
