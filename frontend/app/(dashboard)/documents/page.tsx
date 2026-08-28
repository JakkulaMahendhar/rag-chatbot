"use client";

import { FileText } from "lucide-react";

import { useDocuments } from "@/hooks/use-documents";
import { DocumentUploader } from "@/components/documents/document-uploader";
import { DocumentTable } from "@/components/documents/document-table";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { Skeleton } from "@/components/ui/skeleton";

export default function DocumentsPage() {
  const { data: documents, isLoading, isError, error, refetch } = useDocuments();

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 overflow-y-auto p-6">
      <div>
        <h1 className="text-xl font-semibold">Documents</h1>
        <p className="text-sm text-muted-foreground">
          Upload documents to build your knowledge base.
        </p>
      </div>

      <DocumentUploader />

      {isLoading && (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      )}

      {isError && <ErrorState error={error} onRetry={() => refetch()} />}

      {documents && documents.length === 0 && (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          description="Upload your first document above to start building your knowledge base."
        />
      )}

      {documents && documents.length > 0 && (
        <div className="rounded-lg border">
          <DocumentTable documents={documents} />
        </div>
      )}
    </div>
  );
}
