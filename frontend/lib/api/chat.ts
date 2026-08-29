import { apiClient } from "@/lib/api/client";
import type { ChatRequest, ChatResponse, ChatStreamEvent } from "@/types/chat";

export const chatApi = {
  // Single blocking JSON response - kept around for anything that wants
  // the complete answer in one shot (not currently used by the chat UI,
  // which uses `stream` below).
  send: (payload: ChatRequest) => apiClient.post<ChatResponse>("/chat", { body: payload }),
  // Same RAG pipeline as `send`, but reveals the already-decided final
  // answer a chunk at a time - see types/chat.ts for why this isn't
  // token-level LLM streaming.
  stream: (payload: ChatRequest) => apiClient.stream<ChatStreamEvent>("/chat/stream", payload),
};
