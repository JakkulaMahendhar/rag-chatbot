"use client";

import { useState } from "react";
import { Loader2, Search as SearchIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SearchResultCard } from "@/components/search/search-result-card";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { useSearch } from "@/hooks/use-search";

const MIN_QUERY_LENGTH = 3;

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const search = useSearch();

  const runSearch = () => {
    if (query.trim().length < MIN_QUERY_LENGTH) return;
    search.mutate({ query: query.trim() });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runSearch();
  };

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 overflow-y-auto p-6">
      <div>
        <h1 className="text-xl font-semibold">Search your knowledge base</h1>
        <p className="text-sm text-muted-foreground">
          Semantic search across the documents you&apos;ve uploaded.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a search query..."
          aria-label="Search query"
        />
        <Button type="submit" disabled={search.isPending || query.trim().length < MIN_QUERY_LENGTH}>
          {search.isPending ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <SearchIcon className="size-4" />
          )}
          Search
        </Button>
      </form>

      {search.isError && <ErrorState error={search.error} onRetry={runSearch} />}

      {search.isSuccess && search.data.results.length === 0 && (
        <EmptyState
          icon={SearchIcon}
          title="No results"
          description="Try a different question or search phrase."
        />
      )}

      {search.isSuccess && search.data.results.length > 0 && (
        <div className="space-y-3">
          {search.data.results.map((result) => (
            <SearchResultCard key={result.chunk_id} result={result} />
          ))}
        </div>
      )}
    </div>
  );
}
