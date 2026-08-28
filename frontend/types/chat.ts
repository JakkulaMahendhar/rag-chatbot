// Mirrors app/api/chat.py request body and the dict returned by
// app/services/rag_chat.py RAGChatService.chat() (see source_builder.py
// for SourceReference, app/models/source.py for its exact fields).
//
// No streaming today - /chat is a single blocking JSON response.
// No page numbers - PDF text is parsed as one concatenated string,
// page boundaries aren't preserved (see app/services/parser.py).

export interface ChatRequest {
  question: string;
  conversation_id?: string | null;
}

export interface SourceReference {
  document_id: string;
  chunk_id: string;
  filename: string;
  content: string;
  score: number | null;
  rerank_score: number | null;
}

interface EvaluationSummary {
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
