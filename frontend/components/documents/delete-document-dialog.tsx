"use client";

import { Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { useDeleteDocument } from "@/hooks/use-documents";
import { isApiError } from "@/lib/auth/auth-context";

export function DeleteDocumentDialog({
  documentId,
  filename,
}: {
  documentId: number;
  filename: string;
}) {
  const deleteDocument = useDeleteDocument();

  return (
    <AlertDialog>
      <AlertDialogTrigger
        render={<Button variant="destructive" size="icon-sm" aria-label={`Delete ${filename}`} />}
      >
        <Trash2 className="size-4" />
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete &ldquo;{filename}&rdquo;?</AlertDialogTitle>
          <AlertDialogDescription>
            This removes the document, its vector embeddings, and its search index entries. This
            can&apos;t be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel render={<Button variant="outline" />}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            render={<Button variant="destructive" disabled={deleteDocument.isPending} />}
            onClick={() => {
              deleteDocument.mutate(documentId, {
                onSuccess: () => toast.success(`${filename} deleted.`),
                onError: (error) => {
                  toast.error(isApiError(error) ? error.message : "Delete failed.");
                },
              });
            }}
          >
            {deleteDocument.isPending && <Loader2 className="size-4 animate-spin" />}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
