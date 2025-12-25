"use client";

import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useConversionStore } from "@/lib/store";
import { FileArchive, Images } from "lucide-react";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function FileList() {
  const files = useConversionStore((s) => s.files);
  const selectedFileIds = useConversionStore((s) => s.selectedFileIds);
  const toggleFileSelection = useConversionStore((s) => s.toggleFileSelection);
  const selectAllFiles = useConversionStore((s) => s.selectAllFiles);
  const setSelectedFileIds = useConversionStore((s) => s.setSelectedFileIds);

  const allSelected = files.length > 0 && selectedFileIds.length === files.length;
  const someSelected = selectedFileIds.length > 0 && selectedFileIds.length < files.length;

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedFileIds([]);
    } else {
      selectAllFiles();
    }
  };

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
                aria-label="Select all"
              />
            </TableHead>
            <TableHead>File</TableHead>
            <TableHead className="text-right">Size</TableHead>
            <TableHead className="text-right">Pages</TableHead>
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
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
