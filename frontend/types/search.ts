// Mirrors app/schemas/search.py and app/models/search.py

export interface SearchRequest {
  query: string;
  top_k?: number;
}

export interface SearchResult {
  chunk_id: string;
  document: string;
  metadata: Record<string, unknown>;
  score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}
