"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useTranslations } from "next-intl";
import { Upload, FileArchive, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadFiles, suggestFileOrder } from "@/lib/api";
import { useConversionStore } from "@/lib/store";
import { toast } from "sonner";

const ACCEPTED_TYPES = {
  // Archives
  "application/x-cbr": [".cbr"],
  "application/x-cbz": [".cbz"],
  "application/zip": [".zip"],
  "application/x-rar-compressed": [".rar"],
  "application/epub+zip": [".epub"],
  // Images
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/webp": [".webp"],
  "image/gif": [".gif"],
  "image/bmp": [".bmp"],
  "image/tiff": [".tiff", ".tif"],
};

export function FileDropzone() {
  const t = useTranslations("upload");
  const tCommon = useTranslations("common");
  const [isUploading, setIsUploading] = useState(false);
  const setSession = useConversionStore((s) => s.setSession);
  const setMetadata = useConversionStore((s) => s.setMetadata);
  const setFileOrder = useConversionStore((s) => s.setFileOrder);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      setIsUploading(true);
      try {
        const response = await uploadFiles(acceptedFiles);
        setSession(response.session_id, response.files);

        // Auto-order files by parsing filenames (Issue #1, Issue #2, etc.)
        if (response.files.length > 1) {
          try {
            const suggestedOrder = await suggestFileOrder(response.session_id);
            setFileOrder(suggestedOrder);
          } catch {
            // Fallback to upload order if suggestion fails
          }
        }

        // Auto-populate title from first file name
        if (response.files.length > 0) {
          const firstName = response.files[0].original_name;
          const baseName = firstName.replace(/\.(cbr|cbz|zip|rar|epub|images)$/i, "");
          setMetadata({ title: baseName, series: baseName });
        }

        toast.success(`${response.files.length} file(s) uploaded`);
      } catch (error) {
        toast.error(
          error instanceof Error ? error.message : "Failed to upload files"
        );
      } finally {
        setIsUploading(false);
      }
    },
    [setSession, setMetadata, setFileOrder]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    disabled: isUploading,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors cursor-pointer",
        isDragActive
          ? "border-primary bg-primary/5"
          : "border-muted-foreground/25 hover:border-primary/50",
        isUploading && "pointer-events-none opacity-50"
      )}
    >
      <input {...getInputProps()} />

      {isUploading ? (
        <>
          <Loader2 className="h-12 w-12 text-muted-foreground animate-spin" />
          <p className="mt-4 text-lg font-medium">{tCommon("loading")}</p>
        </>
      ) : isDragActive ? (
        <>
          <Upload className="h-12 w-12 text-primary" />
          <p className="mt-4 text-lg font-medium">Drop files here</p>
        </>
      ) : (
        <>
          <FileArchive className="h-12 w-12 text-muted-foreground" />
          <p className="mt-4 text-lg font-medium">
            {t("dropzone.title")}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            {t("dropzone.subtitle")}
          </p>
          <p className="mt-4 text-xs text-muted-foreground">
            {t("dropzone.formats")}
          </p>
        </>
      )}
    </div>
  );
}
