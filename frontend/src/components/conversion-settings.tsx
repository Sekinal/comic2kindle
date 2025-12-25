"use client";

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
import { useConversionStore } from "@/lib/store";
import type { OutputFormat } from "@/types";

const FORMAT_OPTIONS: { value: OutputFormat; label: string; description: string }[] = [
  {
    value: "epub",
    label: "EPUB",
    description: "Recommended for modern Kindle devices (2022+)",
  },
  {
    value: "mobi",
    label: "MOBI",
    description: "Legacy format for older Kindle devices",
  },
  {
    value: "both",
    label: "Both",
    description: "Generate both EPUB and MOBI files",
  },
];

export function ConversionSettings() {
  const outputFormat = useConversionStore((s) => s.outputFormat);
  const setOutputFormat = useConversionStore((s) => s.setOutputFormat);
  const namingPattern = useConversionStore((s) => s.namingPattern);
  const setNamingPattern = useConversionStore((s) => s.setNamingPattern);
  const metadata = useConversionStore((s) => s.metadata);

  // Generate preview of naming pattern
  const previewName = namingPattern
    .replace("{series}", metadata.series || "Manga")
    .replace("{title}", metadata.title || "Title")
    .replace("{index:03d}", String(metadata.series_index).padStart(3, "0"))
    .replace("{index}", String(metadata.series_index));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Conversion Settings</CardTitle>
        <CardDescription>
          Configure output format and file naming
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Output Format */}
        <div className="space-y-3">
          <Label>Output Format</Label>
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
                      Recommended
                    </Badge>
                  )}
                </div>
                <span className="mt-1 text-xs text-muted-foreground">
                  {option.description}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Naming Pattern */}
        <div className="space-y-3">
          <Label htmlFor="naming-pattern">File Naming Pattern</Label>
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
            Available variables: {"{series}"}, {"{title}"}, {"{index}"}, {"{index:03d}"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
