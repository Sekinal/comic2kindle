"use client";

import { useState, useMemo } from "react";
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
  const tChapter = useTranslations("chapter");
  const [showSearch, setShowSearch] = useState(false);
  const metadata = useConversionStore((s) => s.metadata);
  const setMetadata = useConversionStore((s) => s.setMetadata);
  const setChapterInfo = useConversionStore((s) => s.setChapterInfo);

  // Generate title preview
  const titlePreview = useMemo(() => {
    const { chapter_info, title_format, series, title } = metadata;
    let chapterStr = "";
    if (chapter_info.chapter_start !== null && chapter_info.chapter_end !== null) {
      chapterStr = `${chapter_info.chapter_start}-${chapter_info.chapter_end}`;
    } else if (chapter_info.chapter_start !== null) {
      chapterStr = String(chapter_info.chapter_start);
    }
    const volumeStr = chapter_info.volume ? `Vol. ${chapter_info.volume}` : "";

    return title_format
      .replace("{series}", series || title || "Series")
      .replace("{title}", title || "Title")
      .replace("{chapter}", chapterStr || "1")
      .replace("{volume}", volumeStr)
      .replace("{prefix}", chapter_info.title_prefix)
      .replace("{suffix}", chapter_info.title_suffix)
      .trim();
  }, [metadata]);

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

              <div className="grid gap-2">
                <Label htmlFor="series">{t("fields.series")}</Label>
                <Input
                  id="series"
                  placeholder={t("fields.series")}
                  value={metadata.series}
                  onChange={(e) => setMetadata({ series: e.target.value })}
                />
              </div>

              {/* Chapter Information */}
              <div className="space-y-3 pt-2 border-t">
                <Label className="text-sm font-medium">{tChapter("title")}</Label>

                <div className="grid grid-cols-3 gap-3">
                  <div className="grid gap-2">
                    <Label htmlFor="chapter_start" className="text-xs text-muted-foreground">
                      {tChapter("start")}
                    </Label>
                    <Input
                      id="chapter_start"
                      type="number"
                      step="0.5"
                      min={0}
                      placeholder="1"
                      value={metadata.chapter_info.chapter_start ?? ""}
                      onChange={(e) =>
                        setChapterInfo({
                          chapter_start: e.target.value ? parseFloat(e.target.value) : null,
                        })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="chapter_end" className="text-xs text-muted-foreground">
                      {tChapter("end")}
                    </Label>
                    <Input
                      id="chapter_end"
                      type="number"
                      step="0.5"
                      min={0}
                      placeholder="16"
                      value={metadata.chapter_info.chapter_end ?? ""}
                      onChange={(e) =>
                        setChapterInfo({
                          chapter_end: e.target.value ? parseFloat(e.target.value) : null,
                        })
                      }
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="volume" className="text-xs text-muted-foreground">
                      {tChapter("volume")} <span className="text-muted-foreground/60">({tChapter("volumeOptional")})</span>
                    </Label>
                    <Input
                      id="volume"
                      type="number"
                      min={1}
                      placeholder="1"
                      value={metadata.chapter_info.volume ?? ""}
                      onChange={(e) =>
                        setChapterInfo({
                          volume: e.target.value ? parseInt(e.target.value) : null,
                        })
                      }
                    />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">{tChapter("rangeHelp")}</p>
              </div>

              {/* Title Format */}
              <div className="space-y-3 pt-2 border-t">
                <div className="grid gap-2">
                  <Label htmlFor="title_format">{tChapter("titleFormat")}</Label>
                  <Input
                    id="title_format"
                    placeholder="{series} - Ch. {chapter}"
                    value={metadata.title_format}
                    onChange={(e) => setMetadata({ title_format: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground">{tChapter("titleFormatHelp")}</p>
                </div>

                {/* Live Preview */}
                <div className="rounded-md bg-muted p-3">
                  <Label className="text-xs text-muted-foreground">{tChapter("preview")}</Label>
                  <p className="text-sm font-medium mt-1">{titlePreview}</p>
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
