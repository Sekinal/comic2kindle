"use client";

import { useEffect, useRef, useCallback } from "react";
import { useTranslations } from "next-intl";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useConversionStore } from "@/lib/store";
import { getJobStatus, getDownloadUrl, getAllDownloadsUrl } from "@/lib/api";
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Download,
  FileArchive,
  Layers,
  Scissors,
} from "lucide-react";
import type { ConversionStatus } from "@/types";

function getStatusConfig(t: ReturnType<typeof useTranslations>): Record<
  ConversionStatus,
  { label: string; icon: React.ReactNode; color: string }
> {
  return {
    pending: {
      label: t("status.pending"),
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
      color: "text-muted-foreground",
    },
    processing: {
      label: t("status.processing"),
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
      color: "text-blue-500",
    },
    extracting: {
      label: t("status.extracting"),
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
      color: "text-blue-500",
    },
    merging: {
      label: t("status.merging"),
      icon: <Layers className="h-4 w-4 animate-pulse" />,
      color: "text-purple-500",
    },
    splitting: {
      label: t("status.splitting"),
      icon: <Scissors className="h-4 w-4 animate-pulse" />,
      color: "text-orange-500",
    },
    converting: {
      label: t("status.converting"),
      icon: <Loader2 className="h-4 w-4 animate-spin" />,
      color: "text-yellow-500",
    },
    completed: {
      label: t("status.completed"),
      icon: <CheckCircle2 className="h-4 w-4" />,
      color: "text-green-500",
    },
    failed: {
      label: t("status.failed"),
      icon: <XCircle className="h-4 w-4" />,
      color: "text-red-500",
    },
  };
}

export function ProgressTracker() {
  const t = useTranslations("progress");
  const currentJob = useConversionStore((s) => s.currentJob);
  const sessionId = useConversionStore((s) => s.sessionId);
  const setCurrentJob = useConversionStore((s) => s.setCurrentJob);

  const STATUS_CONFIG = getStatusConfig(t);

  // Adaptive polling with exponential backoff
  // Start fast (500ms), slow down if no progress, speed up if progressing
  const pollIntervalRef = useRef(500);
  const lastProgressRef = useRef(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const consecutiveErrorsRef = useRef(0);

  const poll = useCallback(async () => {
    if (!currentJob) return;
    if (currentJob.status === "completed" || currentJob.status === "failed") {
      return;
    }

    try {
      const updated = await getJobStatus(currentJob.job_id);
      setCurrentJob(updated);
      consecutiveErrorsRef.current = 0;

      // Calculate progress delta to adapt polling rate
      const progressDelta = updated.progress - lastProgressRef.current;
      lastProgressRef.current = updated.progress;

      // Adaptive interval based on progress rate
      if (progressDelta < 1) {
        // Slow/no progress - back off to reduce server load
        pollIntervalRef.current = Math.min(pollIntervalRef.current * 1.5, 5000);
      } else if (progressDelta >= 5) {
        // Fast progress - poll more frequently for responsive UI
        pollIntervalRef.current = Math.max(pollIntervalRef.current / 1.5, 300);
      } else {
        // Normal progress - moderate interval
        pollIntervalRef.current = Math.max(pollIntervalRef.current / 1.2, 500);
      }

      // Schedule next poll if still in progress
      if (updated.status !== "completed" && updated.status !== "failed") {
        timeoutRef.current = setTimeout(poll, pollIntervalRef.current);
      }
    } catch {
      // On error, back off more aggressively
      consecutiveErrorsRef.current++;
      pollIntervalRef.current = Math.min(
        pollIntervalRef.current * 2,
        10000 // Max 10s on errors
      );

      // Stop polling after 5 consecutive errors
      if (consecutiveErrorsRef.current < 5) {
        timeoutRef.current = setTimeout(poll, pollIntervalRef.current);
      }
    }
  }, [currentJob, setCurrentJob]);

  useEffect(() => {
    if (!currentJob) return;
    if (currentJob.status === "completed" || currentJob.status === "failed") {
      return;
    }

    // Reset polling state for new job
    pollIntervalRef.current = 500;
    lastProgressRef.current = currentJob.progress;
    consecutiveErrorsRef.current = 0;

    // Start polling
    timeoutRef.current = setTimeout(poll, pollIntervalRef.current);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [currentJob?.job_id, currentJob?.status, poll]);

  if (!currentJob) return null;

  const statusConfig = STATUS_CONFIG[currentJob.status];
  const splitInfo = currentJob.split_count > 1
    ? ` (${t("partOf", { current: currentJob.output_files.length + 1, total: currentJob.split_count })})`
    : "";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{t("title")}</span>
          <Badge variant="outline" className={statusConfig.color}>
            {statusConfig.icon}
            <span className="ml-1">{statusConfig.label}{splitInfo}</span>
          </Badge>
        </CardTitle>
        <CardDescription>
          {currentJob.current_file
            ? `${t("processingFile")}: ${currentJob.current_file}`
            : currentJob.status === "completed"
              ? t("allCompleted")
              : currentJob.error || t("preparing")}
          {currentJob.current_phase && ` - ${currentJob.current_phase}`}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{t("progressLabel")}</span>
            <span className="font-medium">{Math.round(currentJob.progress)}%</span>
          </div>
          <Progress value={currentJob.progress} className="h-2" />
        </div>

        {currentJob.status === "completed" && currentJob.output_files.length > 0 && (
          <div className="space-y-3 pt-2">
            <h4 className="text-sm font-medium">{t("downloads")}</h4>
            <div className="space-y-2">
              {currentJob.output_files.map((filename) => (
                <div
                  key={filename}
                  className="flex items-center justify-between p-2 rounded border"
                >
                  <div className="flex items-center gap-2">
                    <FileArchive className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm truncate">{filename}</span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    asChild
                  >
                    <a
                      href={getDownloadUrl(sessionId!, filename)}
                      download={filename}
                    >
                      <Download className="h-4 w-4" />
                    </a>
                  </Button>
                </div>
              ))}
            </div>

            {currentJob.output_files.length > 1 && (
              <Button asChild className="w-full">
                <a href={getAllDownloadsUrl(sessionId!)} download>
                  <Download className="h-4 w-4 mr-2" />
                  {t("downloadAll")}
                </a>
              </Button>
            )}
          </div>
        )}

        {currentJob.status === "failed" && currentJob.error && (
          <div className="p-3 rounded bg-destructive/10 text-destructive text-sm">
            {currentJob.error}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
