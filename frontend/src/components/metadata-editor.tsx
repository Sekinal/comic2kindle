"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useConversionStore } from "@/lib/store";
import { MetadataSearch } from "@/components/metadata-search";
import { Search, Image as ImageIcon } from "lucide-react";
import { getCoverImageUrl } from "@/lib/api";

export function MetadataEditor() {
  const [showSearch, setShowSearch] = useState(false);
  const metadata = useConversionStore((s) => s.metadata);
  const setMetadata = useConversionStore((s) => s.setMetadata);

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Metadata</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSearch(true)}
            >
              <Search className="h-4 w-4 mr-2" />
              Search Online
            </Button>
          </CardTitle>
          <CardDescription>
            Add metadata to your converted files
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-[200px_1fr]">
            {/* Cover Preview */}
            <div className="flex flex-col items-center gap-2">
              <div className="relative w-full aspect-[2/3] bg-muted rounded-lg overflow-hidden">
                {metadata.cover_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={getCoverImageUrl(metadata.cover_url)}
                    alt="Cover"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                    <ImageIcon className="h-12 w-12" />
                  </div>
                )}
              </div>
              <p className="text-xs text-muted-foreground text-center">
                Cover will be auto-extracted if not set
              </p>
            </div>

            {/* Form Fields */}
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  placeholder="Manga Title"
                  value={metadata.title}
                  onChange={(e) => setMetadata({ title: e.target.value })}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="author">Author</Label>
                <Input
                  id="author"
                  placeholder="Author Name"
                  value={metadata.author}
                  onChange={(e) => setMetadata({ author: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="series">Series</Label>
                  <Input
                    id="series"
                    placeholder="Series Name"
                    value={metadata.series}
                    onChange={(e) => setMetadata({ series: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="series_index">Volume/Chapter #</Label>
                  <Input
                    id="series_index"
                    type="number"
                    min={1}
                    value={metadata.series_index}
                    onChange={(e) =>
                      setMetadata({ series_index: parseInt(e.target.value) || 1 })
                    }
                  />
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="description">Description</Label>
                <textarea
                  id="description"
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  placeholder="Brief description..."
                  value={metadata.description}
                  onChange={(e) => setMetadata({ description: e.target.value })}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <MetadataSearch open={showSearch} onOpenChange={setShowSearch} />
    </>
  );
}
