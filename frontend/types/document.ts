// Mirrors app/schemas/document.py and app/schemas/upload.py

export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface DocumentResponse {
  id: number;
  filename: string;
  file_path: string;
  uploaded_at: string;
  status: DocumentStatus;
  error_message: string | null;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  message: string;
}
