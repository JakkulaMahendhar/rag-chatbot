"use client";

import { useRef, useState } from "react";
import { Loader2, Upload } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useUploadDocument } from "@/hooks/use-documents";
import { isApiError } from "@/lib/auth/auth-context";

// Mirrors ALLOWED_TYPES in app/api/upload.py - client-side check is just
// UX, the backend re-validates and is authoritative.
const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"];

export function DocumentUploader() {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadDocument();

  const handleFile = (file: File) => {
    const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      toast.error(`Unsupported file type. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`);
      return;
    }

    upload.mutate(file, {
      onSuccess: () => toast.success(`${file.name} uploaded and queued for processing.`),
      onError: (error) => {
        toast.error(isApiError(error) ? error.message : "Upload failed. Please try again.");
      },
    });
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-8 text-center transition-colors",
        isDragging ? "border-primary bg-primary/5" : "hover:bg-muted/50",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED_EXTENSIONS.join(",")}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />

      {upload.isPending ? (
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      ) : (
        <Upload className="size-6 text-muted-foreground" />
      )}

      <p className="text-sm font-medium">
        {upload.isPending ? "Uploading..." : "Drop a file here or click to browse"}
      </p>
      <p className="text-xs text-muted-foreground">
        Supports {ALLOWED_EXTENSIONS.join(", ")}
      </p>

      <Button type="button" variant="outline" size="sm" disabled={upload.isPending} className="mt-2">
        Choose file
      </Button>
    </div>
  );
}
