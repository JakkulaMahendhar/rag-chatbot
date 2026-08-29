// Mirrors app/api/chat.py request body and the dict returned by
// app/services/rag_chat.py RAGChatService.chat() (see source_builder.py
// for SourceReference, app/models/source.py for its exact fields).
//
// POST /chat/stream reveals the same already-final answer over Server-
// Sent Events instead of one JSON blob - see ChatStreamEvent below. It's
// not token-level LLM streaming: the hallucination guard still runs to
// completion first, same as POST /chat.
// No page numbers - PDF text is parsed as one concatenated string,
// page boundaries aren't preserved (see app/services/parser.py).

export interface ChatRequest {
  question: string;
  conversation_id?: string | null;
  // Optional override of the server's default LLM - see lib/llm-provider.ts.
  llm_provider?: "ollama" | "gemini" | null;
}

export interface SourceReference {
  document_id: string;
  chunk_id: string;
  filename: string;
  content: string;
  score: number | null;
  rerank_score: number | null;
}

export interface EvaluationSummary {
  average_score: number;
  best_score: number;
  quality: string;
}

export interface ChatResponse {
  conversation_id: string;
  question: string;
  answer: string;
  sources: SourceReference[];
  search_evaluation: EvaluationSummary & { question: string; retrieved: number };
  evaluation: EvaluationSummary;
}

export interface ChatStreamTokenEvent {
  type: "token";
  content: string;
}

export interface ChatStreamDoneEvent {
  type: "done";
  conversation_id: string;
  sources: SourceReference[];
  search_evaluation: EvaluationSummary & { question: string; retrieved: number };
}

export type ChatStreamEvent = ChatStreamTokenEvent | ChatStreamDoneEvent;
