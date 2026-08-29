export type LlmProvider = "ollama" | "gemini";

const STORAGE_KEY = "rag_chatbot_llm_provider";

const DEFAULT_PROVIDER: LlmProvider = "ollama";

/**
 * Per-browser preference for which LLM answers chat questions - mirrors
 * app/api/chat.py's optional `llm_provider` field. Not tied to the user's
 * account, same as tokenStorage isn't: this is a client-side convenience,
 * not a synced setting. Falls back to "ollama" (the server's own default,
 * see app/core/config.py's Settings.llm_provider) if nothing is stored.
 */
export const llmProviderStorage = {
  get(): LlmProvider {
    if (typeof window === "undefined") return DEFAULT_PROVIDER;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === "gemini" ? "gemini" : DEFAULT_PROVIDER;
  },
  set(provider: LlmProvider) {
    window.localStorage.setItem(STORAGE_KEY, provider);
  },
};
