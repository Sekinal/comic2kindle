"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileArchive, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadFiles } from "@/lib/api";
import { useConversionStore } from "@/lib/store";
import { toast } from "sonner";

const ACCEPTED_TYPES = {
  "application/x-cbr": [".cbr"],
  "application/x-cbz": [".cbz"],
  "application/zip": [".zip"],
  "application/x-rar-compressed": [".rar"],
};

export function FileDropzone() {
  const [isUploading, setIsUploading] = useState(false);
  const setSession = useConversionStore((s) => s.setSession);
  const setMetadata = useConversionStore((s) => s.setMetadata);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      setIsUploading(true);
      try {
        const response = await uploadFiles(acceptedFiles);
        setSession(response.session_id, response.files);

        // Auto-populate title from first file name
        if (response.files.length > 0) {
          const firstName = response.files[0].original_name;
          const baseName = firstName.replace(/\.(cbr|cbz|zip|rar)$/i, "");
          setMetadata({ title: baseName, series: baseName });
        }

        toast.success(`Uploaded ${response.files.length} file(s)`);
      } catch (error) {
        toast.error(
          error instanceof Error ? error.message : "Failed to upload files"
        );
      } finally {
        setIsUploading(false);
      }
    },
    [setSession, setMetadata]
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
          <p className="mt-4 text-lg font-medium">Uploading...</p>
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
            Drag & drop manga files here
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            or click to select files
          </p>
          <p className="mt-4 text-xs text-muted-foreground">
            Supported formats: CBR, CBZ, ZIP, RAR
          </p>
        </>
      )}
    </div>
  );
}
