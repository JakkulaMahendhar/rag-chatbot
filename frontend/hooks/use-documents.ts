"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { documentsApi } from "@/lib/api/documents";
import type { DocumentResponse } from "@/types/document";

const DOCUMENTS_KEY = ["documents"];

function hasActiveJob(documents: DocumentResponse[] | undefined) {
  return documents?.some((doc) => doc.status === "pending" || doc.status === "processing") ?? false;
}

export function useDocuments() {
  return useQuery({
    queryKey: DOCUMENTS_KEY,
    queryFn: documentsApi.list,
    // Poll only while something is actually pending/processing - the
    // real worker (app/worker.py) picks jobs up every 5s, so 3s here
    // catches transitions promptly without polling forever once
    // everything has settled into completed/failed.
    refetchInterval: (query) => (hasActiveJob(query.state.data) ? 3000 : false),
  });
}

export function useDocument(id: number | null) {
  return useQuery({
    queryKey: ["documents", id],
    queryFn: () => documentsApi.get(id as number),
    enabled: id !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "processing" ? 3000 : false;
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: documentsApi.upload,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY }),
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY }),
  });
}
