"use client";

import { useCallback, useState } from "react";

import { chatApi } from "@/lib/api/chat";
import { isApiError } from "@/lib/auth/auth-context";
import { llmProviderStorage } from "@/lib/llm-provider";
import type { SourceReference } from "@/types/chat";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
  quality?: string;
  bestScore?: number;
  error?: string;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  const sendMessage = useCallback(
    async (question: string) => {
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: question,
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsPending(true);

      try {
        // No streaming - see types/chat.ts. This resolves only once
        // the full answer is ready.
        const response = await chatApi.send({
          question,
          conversation_id: conversationId,
          llm_provider: llmProviderStorage.get(),
        });

        setConversationId(response.conversation_id);
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: response.answer,
            sources: response.sources,
            quality: response.search_evaluation?.quality,
            bestScore: response.search_evaluation?.best_score,
          },
        ]);
      } catch (error) {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "",
            error: isApiError(error) ? error.message : "Something went wrong.",
          },
        ]);
      } finally {
        setIsPending(false);
      }
    },
    [conversationId],
  );

  const startNewConversation = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  return { messages, isPending, sendMessage, startNewConversation };
}
