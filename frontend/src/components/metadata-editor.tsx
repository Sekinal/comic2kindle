"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
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
  const t = useTranslations("metadata");
  const [showSearch, setShowSearch] = useState(false);
  const metadata = useConversionStore((s) => s.metadata);
  const setMetadata = useConversionStore((s) => s.setMetadata);

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>{t("title")}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSearch(true)}
            >
              <Search className="h-4 w-4 mr-2" />
              {t("searchOnline")}
            </Button>
          </CardTitle>
          <CardDescription>
            {t("description")}
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
                {t("coverHint")}
              </p>
            </div>

            {/* Form Fields */}
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="title">{t("fields.title")}</Label>
                <Input
                  id="title"
                  placeholder={t("fields.title")}
                  value={metadata.title}
                  onChange={(e) => setMetadata({ title: e.target.value })}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="author">{t("fields.author")}</Label>
                <Input
                  id="author"
                  placeholder={t("fields.author")}
                  value={metadata.author}
                  onChange={(e) => setMetadata({ author: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="series">{t("fields.series")}</Label>
                  <Input
                    id="series"
                    placeholder={t("fields.series")}
                    value={metadata.series}
                    onChange={(e) => setMetadata({ series: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="series_index">{t("fields.volume")}</Label>
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
                <Label htmlFor="description">{t("fields.description")}</Label>
                <textarea
                  id="description"
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  placeholder={t("fields.description")}
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
