# LLM Integration

How this project connects to a Large Language Model. For the full
generation → hallucination-guard flow in context, see
[`docs/RAG_PIPELINE.md`, sections 11–13](RAG_PIPELINE.md#11-llm-integration).

## LLM Abstraction

**File:** `app/services/llm/base.py`

```python
class LLMService(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...
```

One method, implemented by two classes. Every caller in this codebase
(`RAGChatService`, `QueryEnhancer`, `QueryExpander`,
`HallucinationGuardService`) calls `self.llm.generate(prompt)` and has no
idea which provider is actually behind it.

## Providers

| | Gemini | Ollama |
|---|---|---|
| File | `app/services/llm/gemini.py` | `app/services/llm/ollama.py` |
| SDK | `google-generativeai` | `ollama` (Python client) |
| Model | `gemini-3.6-flash` | `llama3.1` |
| Env var(s) | `GEMINI_API_KEY`, `GEMINI_MODEL` | `OLLAMA_MODEL` |
| Requires | A valid API key | A reachable Ollama daemon (local, or `host.docker.internal` from inside Docker) |

```python
# GeminiService.generate()
response = self.model.generate_content(prompt)
return response.text

# OllamaService.generate()
response = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
return response["message"]["content"]
```

## Which provider is used for a given request

`AIServiceRegistry.get_llm(provider)` (`app/core/ai_registry.py`):

```python
provider = provider or settings.llm_provider   # default: "ollama"
if provider not in cls._llms:
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("Gemini is not configured on this server ...")
        cls._llms[provider] = GeminiService()
    elif provider == "ollama":
        cls._llms[provider] = OllamaService()
cls._llms[provider]
```

`provider` is an optional field on the `POST /chat` request body
(`ChatRequest.llm_provider`, `app/api/chat.py`) — the frontend's Settings
page lets a user pick Gemini or Ollama per request, saved in the
browser's `localStorage` and sent with every chat call. If omitted, the
server's `.env`-configured `LLM_PROVIDER` (default `ollama`) is used.
Both provider instances are cached as singletons — the app can serve one
request via Ollama and the next via Gemini without re-initializing either
client.

## Request format

Every call is a single string prompt in, a single string answer out — no
streaming, no function/tool calling, no structured output mode used by
either SDK in this codebase (the JSON responses used by `QueryExpander`
and `HallucinationGuardService` are requested via prompt instructions and
parsed with `json.loads()`, not via a native structured-output API).

## Response parsing

For plain generation, the response is used as-is (`response.text` /
`response["message"]["content"]`). For the two places that need
structured output:

- `QueryExpander.expand()` expects a JSON array; strips a leading
  ` ```json ` fence if present, then `json.loads()`s it. On failure, falls
  back to a line-by-line best-effort parse.
- `HallucinationGuardService._parse_response()` expects a JSON object
  (`{"grounded": ..., "confidence": ..., "unsupported_claims": [...]}`);
  same fence-stripping, and on failure defaults to `{"grounded": False,
  ...}` rather than raising.

Neither uses a schema-validated structured-output feature — both are
prompt-requested JSON, defensively parsed.

## Error handling

`app/api/chat.py` catches two specific failure classes around the whole
pipeline call:

```python
except ValueError as error:                    # e.g. Gemini requested with no API key
    raise HTTPException(status_code=400, ...)

except GoogleAPIError as error:                 # Gemini quota/auth/API failures
    raise HTTPException(status_code=503, detail=f"Gemini API error: {error.message}")
```

Anything else (including any Ollama-specific error — the `ollama` Python
client's own exceptions are not caught anywhere) propagates as an
unhandled exception and surfaces as a generic `500`.

## Token considerations

- **No `max_output_tokens` is configured** for either provider — both use
  the SDK's own default.
- **Prompt-side token budgeting is approximate**, not exact: `ContextWindowManager.estimate_tokens()`
  counts words (`len(text.split())`), not real tokens — see
  [`docs/RAG_PIPELINE.md`, section 10](RAG_PIPELINE.md#10-context-building).
  `tiktoken` is listed in `requirements.txt` but is not imported or used
  anywhere in the app.

## Temperature

**Not configured.** Neither `GeminiService` nor `OllamaService` sets a
`temperature`, `top_p`, or any other sampling parameter — both
`generate_content()` and `ollama.chat()` are called with only `prompt`
(or `messages`), so each SDK's own default sampling behavior applies.

## Fallback behavior

**Not implemented.** If the selected provider's call fails, the request
fails — there is no automatic retry against the other provider, and no
retry-with-backoff around the call itself in this codebase (Gemini's own
underlying gRPC client does its own internal retries on some transient
errors before the exception reaches this code, but that's SDK behavior,
not something implemented here).

## Industry Alternatives

> **INDUSTRY ALTERNATIVE**

| Provider | Notes |
|---|---|
| OpenAI | GPT-family models via the `openai` SDK (installed in `requirements.txt` but not imported anywhere in this app) |
| Anthropic | Claude models |
| Azure OpenAI | OpenAI models via Azure's hosting/compliance wrapper |
| AWS Bedrock | Managed access to several third-party and Amazon model providers behind one API |
| Self-hosted (Llama, Mistral, etc.) | Run your own inference server (e.g. vLLM), full control over weights and cost, more operational responsibility |

None of these are ranked here — which one fits depends on data residency
requirements, cost model, and whether self-hosting is acceptable for the
team operating the system.

## RAG does not train the model

Worth stating plainly, since it's easy to conflate: nothing in this
pipeline fine-tunes, trains, or otherwise permanently modifies either
LLM. Every "customization" is entirely in what gets put into the prompt
at request time — the retrieved context. The model's weights are
identical before and after every request.

```
Documents → Embeddings → Vector DB → Retrieve context → LLM generates from context
```

No training loop, no gradient updates, no fine-tuning job exists anywhere
in this codebase.
