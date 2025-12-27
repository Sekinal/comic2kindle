"use client";

import { useTranslations } from "next-intl";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { useConversionStore } from "@/lib/store";
import type { EpubExtractionMode, OutputFormat } from "@/types";
import { AlertTriangle } from "lucide-react";

export function ConversionSettings() {
  const t = useTranslations("settings");

  const outputFormat = useConversionStore((s) => s.outputFormat);
  const setOutputFormat = useConversionStore((s) => s.setOutputFormat);
  const namingPattern = useConversionStore((s) => s.namingPattern);
  const setNamingPattern = useConversionStore((s) => s.setNamingPattern);
  const metadata = useConversionStore((s) => s.metadata);
  const mergeFiles = useConversionStore((s) => s.mergeFiles);
  const setMergeFiles = useConversionStore((s) => s.setMergeFiles);
  const epubMode = useConversionStore((s) => s.epubMode);
  const setEpubMode = useConversionStore((s) => s.setEpubMode);
  const maxOutputSizeMb = useConversionStore((s) => s.maxOutputSizeMb);
  const setMaxOutputSizeMb = useConversionStore((s) => s.setMaxOutputSizeMb);
  const hasEpubFiles = useConversionStore((s) => s.hasEpubFiles);
  const estimatedTotalSize = useConversionStore((s) => s.estimatedTotalSize);
  const files = useConversionStore((s) => s.files);

  const FORMAT_OPTIONS: { value: OutputFormat; label: string; description: string }[] = [
    {
      value: "epub",
      label: t("outputFormat.epub"),
      description: "",
    },
    {
      value: "mobi",
      label: t("outputFormat.mobi"),
      description: "",
    },
    {
      value: "both",
      label: t("outputFormat.both"),
      description: "",
    },
  ];

  const EPUB_MODE_OPTIONS: { value: EpubExtractionMode; label: string; description: string }[] = [
    {
      value: "images_only",
      label: t("epubMode.imagesOnly"),
      description: t("epubMode.imagesOnlyDesc"),
    },
    {
      value: "preserve",
      label: t("epubMode.preserve"),
      description: t("epubMode.preserveDesc"),
    },
  ];

  // Generate preview of naming pattern
  const previewName = namingPattern
    .replace("{series}", metadata.series || "Manga")
    .replace("{title}", metadata.title || "Title")
    .replace("{index:03d}", String(metadata.series_index).padStart(3, "0"))
    .replace("{index}", String(metadata.series_index));

  // Calculate estimated split count
  const totalSizeBytes = estimatedTotalSize();
  const maxSizeBytes = maxOutputSizeMb * 1024 * 1024;
  const estimatedSplitCount = mergeFiles && totalSizeBytes > maxSizeBytes
    ? Math.ceil(totalSizeBytes / maxSizeBytes)
    : 1;

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>
          {t("namingPattern.help")}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Merge Files Option */}
        {files.length > 1 && (
          <div className="flex items-start space-x-3 rounded-lg border p-4">
            <Checkbox
              id="merge-files"
              checked={mergeFiles}
              onCheckedChange={(checked) => setMergeFiles(checked === true)}
            />
            <div className="space-y-1">
              <Label htmlFor="merge-files" className="cursor-pointer font-medium">
                {t("mergeFiles.label")}
              </Label>
              <p className="text-sm text-muted-foreground">
                {t("mergeFiles.description")}
              </p>
            </div>
          </div>
        )}

        {/* EPUB Mode (only show if EPUB files are present) */}
        {hasEpubFiles() && (
          <div className="space-y-3">
            <Label>{t("epubMode.label")}</Label>
            <div className="grid gap-3 sm:grid-cols-2">
              {EPUB_MODE_OPTIONS.map((option) => (
                <div
                  key={option.value}
                  onClick={() => setEpubMode(option.value)}
                  className={`relative flex cursor-pointer flex-col rounded-lg border p-4 transition-colors ${
                    epubMode === option.value
                      ? "border-primary bg-primary/5"
                      : "hover:border-primary/50"
                  }`}
                >
                  <span className="font-medium">{option.label}</span>
                  <span className="mt-1 text-xs text-muted-foreground">
                    {option.description}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Max Output Size (only show when merging) */}
        {mergeFiles && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>{t("maxSize.label")}</Label>
              <span className="text-sm font-medium">{maxOutputSizeMb} MB</span>
            </div>
            <Slider
              value={[maxOutputSizeMb]}
              onValueChange={([value]) => setMaxOutputSizeMb(value)}
              min={50}
              max={500}
              step={10}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              {t("maxSize.description")}
            </p>

            {/* Estimated size and split warning */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{t("estimatedSize")}:</span>
              <span className="font-medium">{formatBytes(totalSizeBytes)}</span>
            </div>

            {estimatedSplitCount > 1 && (
              <div className="flex items-center gap-2 rounded-md bg-yellow-500/10 p-3 text-sm text-yellow-600 dark:text-yellow-500">
                <AlertTriangle className="h-4 w-4" />
                <span>{t("splitWarning", { count: estimatedSplitCount })}</span>
              </div>
            )}
          </div>
        )}

        {/* Output Format */}
        <div className="space-y-3">
          <Label>{t("outputFormat.label")}</Label>
          <div className="grid gap-3 sm:grid-cols-3">
            {FORMAT_OPTIONS.map((option) => (
              <div
                key={option.value}
                onClick={() => setOutputFormat(option.value)}
                className={`relative flex cursor-pointer flex-col rounded-lg border p-4 transition-colors ${
                  outputFormat === option.value
                    ? "border-primary bg-primary/5"
                    : "hover:border-primary/50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{option.label}</span>
                  {option.value === "epub" && (
                    <Badge variant="secondary" className="text-xs">
                      Rec
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Naming Pattern */}
        <div className="space-y-3">
          <Label htmlFor="naming-pattern">{t("namingPattern.label")}</Label>
          <Input
            id="naming-pattern"
            value={namingPattern}
            onChange={(e) => setNamingPattern(e.target.value)}
            placeholder="{series} - Chapter {index:03d}"
          />
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Preview:</span>
            <code className="bg-muted px-2 py-1 rounded">
              {previewName}.epub
            </code>
          </div>
          <p className="text-xs text-muted-foreground">
            {t("namingPattern.help")}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
