"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { useConversionStore } from "@/lib/store";
import { deleteFile } from "@/lib/api";
import { FileArchive, Images, Trash2, Loader2 } from "lucide-react";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function FileList() {
  const t = useTranslations("upload.fileList");
  const tCommon = useTranslations("common");
  const files = useConversionStore((s) => s.files);
  const selectedFileIds = useConversionStore((s) => s.selectedFileIds);
  const toggleFileSelection = useConversionStore((s) => s.toggleFileSelection);
  const selectAllFiles = useConversionStore((s) => s.selectAllFiles);
  const setSelectedFileIds = useConversionStore((s) => s.setSelectedFileIds);
  const sessionId = useConversionStore((s) => s.sessionId);
  const removeFile = useConversionStore((s) => s.removeFile);

  const [fileToDelete, setFileToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const allSelected = files.length > 0 && selectedFileIds.length === files.length;
  const someSelected = selectedFileIds.length > 0 && selectedFileIds.length < files.length;

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedFileIds([]);
    } else {
      selectAllFiles();
    }
  };

  const handleDeleteFile = async () => {
    if (!fileToDelete || !sessionId) return;

    setIsDeleting(true);
    try {
      await deleteFile(sessionId, fileToDelete);
      removeFile(fileToDelete);
    } catch (error) {
      console.error("Failed to delete file:", error);
    } finally {
      setIsDeleting(false);
      setFileToDelete(null);
    }
  };

  const fileToDeleteName = files.find((f) => f.id === fileToDelete)?.original_name;

  if (files.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                checked={allSelected}
                ref={(el) => {
                  if (el) {
                    (el as HTMLButtonElement).dataset.state = someSelected
                      ? "indeterminate"
                      : allSelected
                        ? "checked"
                        : "unchecked";
                  }
                }}
                onCheckedChange={handleSelectAll}
                aria-label={t("selectAll")}
              />
            </TableHead>
            <TableHead>{t("file")}</TableHead>
            <TableHead className="text-right">{t("size")}</TableHead>
            <TableHead className="text-right">{t("pages")}</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {files.map((file) => (
            <TableRow key={file.id}>
              <TableCell>
                <Checkbox
                  checked={selectedFileIds.includes(file.id)}
                  onCheckedChange={() => toggleFileSelection(file.id)}
                  aria-label={`Select ${file.original_name}`}
                />
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <FileArchive className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">{file.original_name}</span>
                  <Badge variant="outline" className="text-xs">
                    {file.extension.toUpperCase().replace(".", "")}
                  </Badge>
                </div>
              </TableCell>
              <TableCell className="text-right text-muted-foreground">
                {formatBytes(file.size)}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-1 text-muted-foreground">
                  <Images className="h-3 w-3" />
                  <span>{file.page_count || "?"}</span>
                </div>
              </TableCell>
              <TableCell>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  onClick={() => setFileToDelete(file.id)}
                  aria-label={t("removeFile")}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <AlertDialog open={!!fileToDelete} onOpenChange={(open) => !open && setFileToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("removeFile")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("confirmRemove")}
              {fileToDeleteName && (
                <span className="block mt-2 font-medium text-foreground">
                  {fileToDeleteName}
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>{tCommon("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteFile}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {tCommon("loading")}
                </>
              ) : (
                tCommon("remove")
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
