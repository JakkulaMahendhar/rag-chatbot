"use client";

import { useDocuments } from "@/hooks/use-documents";

/**
 * Chunk/source metadata stores the on-disk (UUID-based) storage filename,
 * not the originally uploaded name (see app/services/document_processor.py
 * - chunks are tagged with `location.name`, the StorageService path).
 * The documents list already has the real filename per document_id, so
 * prefer that - this joins two real API responses, it doesn't invent
 * anything. Falls back to the raw metadata filename if the document
 * isn't in the (still-loading, or since-deleted) documents list.
 */
export function useDocumentFilename(documentId: string | null, fallback: string | null) {
  const { data: documents } = useDocuments();

  return documents?.find((doc) => String(doc.id) === documentId)?.filename ?? fallback;
}
