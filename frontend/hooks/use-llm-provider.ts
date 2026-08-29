"use client";

import { useCallback, useState } from "react";

import { llmProviderStorage, type LlmProvider } from "@/lib/llm-provider";

export function useLlmProvider() {
  const [provider, setProviderState] = useState<LlmProvider>(() => llmProviderStorage.get());

  const setProvider = useCallback((next: LlmProvider) => {
    llmProviderStorage.set(next);
    setProviderState(next);
  }, []);

  return { provider, setProvider };
}
