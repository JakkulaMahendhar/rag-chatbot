"use client";

import { useState } from "react";
import { ChevronDown, FileText } from "lucide-react";

import { cn } from "@/lib/utils";
import { useDocuments } from "@/hooks/use-documents";
import type { SourceReference } from "@/types/chat";

// score is a raw Chroma L2 distance (see hybrid_search.py's own
// _normalize_distance) - lower is better, unbounded. rerank_score (when
// present) is already a 0-1 sigmoid output from Reranker.rerank(), so
// it's shown directly rather than re-transformed.
function relevancePercent(source: SourceReference): number | null {
  if (source.rerank_score !== null) return Math.round(source.rerank_score * 100);
  if (source.score !== null) return Math.round((1 / (1 + Math.max(0, source.score))) * 100);
  return null;
}

export function SourceList({ sources }: { sources: SourceReference[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  // Chunk metadata stores the on-disk (UUID-based) storage filename, not
  // the originally uploaded name (see app/services/document_processor.py
  // - chunks are tagged with `location.name`, the StorageService path).
  // The documents list already has the real filename per document_id
  // (already fetched/cached for the Documents page), so prefer that -
  // this joins two real API responses, it doesn't invent anything.
  const { data: documents } = useDocuments();

  // The backend (app/services/reranker.py) now drops anything below
  // reranker_score_threshold before it ever reaches here, so this
  // shouldn't normally trigger - kept as a defensive display-layer
  // filter rather than trusting every source the API happens to send is
  // actually worth showing Sarah as "based on this."
  const relevantSources = sources.filter((source) => relevancePercent(source) !== 0);

  if (relevantSources.length === 0) return null;

  const displayName = (source: SourceReference) =>
    documents?.find((doc) => String(doc.id) === source.document_id)?.filename ||
    source.filename ||
    "Unknown document";

  return (
    <div className="mt-3 space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground">
        Based on {relevantSources.length} source{relevantSources.length === 1 ? "" : "s"}
      </p>
      {relevantSources.map((source) => {
        const isExpanded = expandedId === source.chunk_id;
        const relevance = relevancePercent(source);

        return (
          <div key={source.chunk_id} className="rounded-md border text-sm">
            <button
              type="button"
              onClick={() => setExpandedId(isExpanded ? null : source.chunk_id)}
              aria-expanded={isExpanded}
              className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left hover:bg-muted/50"
            >
              <span className="flex min-w-0 items-center gap-2">
                <FileText className="size-3.5 shrink-0 text-muted-foreground" />
                <span className="truncate">{displayName(source)}</span>
              </span>
              <span className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
                {relevance !== null && `${relevance}%`}
                <ChevronDown
                  className={cn("size-3.5 transition-transform", isExpanded && "rotate-180")}
                />
              </span>
            </button>
            {isExpanded && (
              <p className="border-t px-3 py-2 text-xs text-muted-foreground">{source.content}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
