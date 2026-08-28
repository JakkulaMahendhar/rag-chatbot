import { apiClient } from "@/lib/api/client";
import type { ChatRequest, ChatResponse } from "@/types/chat";

export const chatApi = {
  // No streaming - see types/chat.ts. Callers should show a loading
  // state for the duration of this request, not an incremental one.
  send: (payload: ChatRequest) => apiClient.post<ChatResponse>("/chat", { body: payload }),
};
