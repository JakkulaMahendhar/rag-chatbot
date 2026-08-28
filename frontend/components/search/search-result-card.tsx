import { FileText } from "lucide-react";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useDocumentFilename } from "@/hooks/use-document-filename";
import type { SearchResult } from "@/types/search";

// result.score is a raw Chroma L2 distance (app/services/search.py
// returns results["distances"] directly) - lower is better, unbounded.
// Converted to an intuitive 0-1 relevance score using the same
// distance -> similarity formula app/services/hybrid_search.py already
// uses (_normalize_distance), rather than inventing a different one.
function toRelevance(distance: number) {
  return 1 / (1 + Math.max(0, distance));
}

export function SearchResultCard({ result }: { result: SearchResult }) {
  const documentId =
    typeof result.metadata?.document_id === "string" ? result.metadata.document_id : null;
  const metadataFilename =
    typeof result.metadata?.filename === "string" ? result.metadata.filename : null;
  const filename = useDocumentFilename(documentId, metadataFilename) ?? "Unknown document";

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
        <div className="flex min-w-0 items-center gap-2">
          <FileText className="size-4 shrink-0 text-muted-foreground" />
          <span className="truncate text-sm font-medium">{filename}</span>
        </div>
        <Badge variant="secondary" className="shrink-0">
          {(toRelevance(result.score) * 100).toFixed(0)}% relevant
        </Badge>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{result.document}</p>
      </CardContent>
    </Card>
  );
}
