import { apiClient } from "@/lib/api/client";
import type { DocumentResponse, UploadResponse } from "@/types/document";

export const documentsApi = {
  list: () => apiClient.get<DocumentResponse[]>("/documents"),

  get: (id: number) => apiClient.get<DocumentResponse>(`/documents/${id}`),

  delete: (id: number) => apiClient.delete<{ message: string }>(`/documents/${id}`),

  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.post<UploadResponse>("/upload", { formData });
  },
};
