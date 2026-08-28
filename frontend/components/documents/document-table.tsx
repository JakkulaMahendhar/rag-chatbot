"use client";

import { FileText } from "lucide-react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { DeleteDocumentDialog } from "@/components/documents/delete-document-dialog";
import type { DocumentResponse } from "@/types/document";

export function DocumentTable({ documents }: { documents: DocumentResponse[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Document</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Uploaded</TableHead>
          <TableHead className="w-px" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((doc) => (
          <TableRow key={doc.id}>
            <TableCell>
              <div className="flex items-center gap-2">
                <FileText className="size-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="truncate font-medium">{doc.filename}</p>
                  {doc.status === "failed" && doc.error_message && (
                    <p className="truncate text-xs text-destructive" title={doc.error_message}>
                      {doc.error_message}
                    </p>
                  )}
                </div>
              </div>
            </TableCell>
            <TableCell>
              <DocumentStatusBadge status={doc.status} />
            </TableCell>
            <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
              {new Date(doc.uploaded_at).toLocaleString()}
            </TableCell>
            <TableCell>
              <DeleteDocumentDialog documentId={doc.id} filename={doc.filename} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
