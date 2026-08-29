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
  // True while this message's answer is still being revealed chunk by
  // chunk - see chat-message.tsx for the blinking-cursor indicator.
  isStreaming?: boolean;
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

      const assistantId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "", isStreaming: true },
      ]);

      try {
        for await (const event of chatApi.stream({
          question,
          conversation_id: conversationId,
          llm_provider: llmProviderStorage.get(),
        })) {
          if (event.type === "token") {
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? { ...message, content: message.content + event.content }
                  : message,
              ),
            );
          } else {
            setConversationId(event.conversation_id);
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      sources: event.sources,
                      quality: event.search_evaluation?.quality,
                      bestScore: event.search_evaluation?.best_score,
                      isStreaming: false,
                    }
                  : message,
              ),
            );
          }
        }
      } catch (error) {
        setMessages((prev) =>
          prev.map((message) =>
            message.id === assistantId
              ? {
                  ...message,
                  error: isApiError(error) ? error.message : "Something went wrong.",
                  isStreaming: false,
                }
              : message,
          ),
        );
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
