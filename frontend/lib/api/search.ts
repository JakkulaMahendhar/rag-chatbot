import { apiClient } from "@/lib/api/client";
import type { SearchRequest, SearchResponse } from "@/types/search";

export const searchApi = {
  search: (payload: SearchRequest) =>
    apiClient.post<SearchResponse>("/search", { body: payload }),
};
