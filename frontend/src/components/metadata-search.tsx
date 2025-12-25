"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search } from "lucide-react";
import { searchMetadata, getCoverImageUrl } from "@/lib/api";
import { useConversionStore } from "@/lib/store";
import type { MetadataSearchResult } from "@/types";
import { toast } from "sonner";

interface MetadataSearchProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MetadataSearch({ open, onOpenChange }: MetadataSearchProps) {
  const metadata = useConversionStore((s) => s.metadata);
  const setMetadata = useConversionStore((s) => s.setMetadata);
  const [query, setQuery] = useState(metadata.title);
  const [results, setResults] = useState<MetadataSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const data = await searchMetadata(query);
      setResults(data);
      if (data.length === 0) {
        toast.info("No results found");
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Search failed"
      );
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelect = (result: MetadataSearchResult) => {
    setMetadata({
      title: result.title,
      author: result.author,
      description: result.description,
      cover_url: result.cover_url,
      series: result.title,
    });
    onOpenChange(false);
    toast.success("Metadata applied");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Search Manga Metadata</DialogTitle>
          <DialogDescription>
            Search MangaDex and AniList for metadata
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-2">
          <Input
            placeholder="Search manga title..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <Button onClick={handleSearch} disabled={isSearching}>
            {isSearching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
          </Button>
        </div>

        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-3">
            {results.map((result) => (
              <div
                key={result.id}
                className="flex gap-4 p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                onClick={() => handleSelect(result)}
              >
                {result.cover_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={getCoverImageUrl(result.cover_url)}
                    alt={result.title}
                    className="w-16 h-24 object-cover rounded"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium truncate">{result.title}</h4>
                    <Badge variant="secondary" className="text-xs shrink-0">
                      {result.source}
                    </Badge>
                  </div>
                  {result.author && (
                    <p className="text-sm text-muted-foreground">
                      by {result.author}
                    </p>
                  )}
                  {result.description && (
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {result.description}
                    </p>
                  )}
                </div>
              </div>
            ))}

            {results.length === 0 && !isSearching && (
              <div className="text-center py-8 text-muted-foreground">
                <Search className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Search for a manga to get started</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
