"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileDropzone } from "@/components/file-dropzone";
import { FileList } from "@/components/file-list";
import { MetadataEditor } from "@/components/metadata-editor";
import { ConversionSettings } from "@/components/conversion-settings";
import { ProgressTracker } from "@/components/progress-tracker";
import { useConversionStore } from "@/lib/store";
import { startConversion, deleteSession } from "@/lib/api";
import { toast } from "sonner";
import {
  ArrowLeft,
  Upload,
  FileText,
  Settings,
  Download,
  Loader2,
  Trash2,
} from "lucide-react";

type WizardStep = "upload" | "metadata" | "settings" | "download";

export default function ConvertPage() {
  const [activeStep, setActiveStep] = useState<WizardStep>("upload");
  const [isConverting, setIsConverting] = useState(false);

  const sessionId = useConversionStore((s) => s.sessionId);
  const files = useConversionStore((s) => s.files);
  const selectedFileIds = useConversionStore((s) => s.selectedFileIds);
  const metadata = useConversionStore((s) => s.metadata);
  const namingPattern = useConversionStore((s) => s.namingPattern);
  const outputFormat = useConversionStore((s) => s.outputFormat);
  const mergeFiles = useConversionStore((s) => s.mergeFiles);
  const fileOrder = useConversionStore((s) => s.fileOrder);
  const epubMode = useConversionStore((s) => s.epubMode);
  const maxOutputSizeMb = useConversionStore((s) => s.maxOutputSizeMb);
  const currentJob = useConversionStore((s) => s.currentJob);
  const setCurrentJob = useConversionStore((s) => s.setCurrentJob);
  const reset = useConversionStore((s) => s.reset);

  const canProceedToMetadata = files.length > 0 && selectedFileIds.length > 0;
  const canProceedToSettings = metadata.title.trim().length > 0;
  const canStartConversion = selectedFileIds.length > 0;

  const handleStartConversion = async () => {
    if (!sessionId || !canStartConversion) return;

    setIsConverting(true);
    try {
      const job = await startConversion({
        session_id: sessionId,
        file_ids: selectedFileIds,
        metadata,
        output_format: outputFormat,
        naming_pattern: namingPattern,
        epub_mode: epubMode,
        merge_files: mergeFiles,
        file_order: fileOrder,
        max_output_size_mb: maxOutputSizeMb,
      });
      setCurrentJob(job);
      setActiveStep("download");
      toast.success("Conversion started");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to start conversion"
      );
    } finally {
      setIsConverting(false);
    }
  };

  const handleReset = async () => {
    if (sessionId) {
      try {
        await deleteSession(sessionId);
      } catch {
        // Ignore cleanup errors
      }
    }
    reset();
    setActiveStep("upload");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild>
              <Link href="/">
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <h1 className="text-xl font-semibold">Convert Manga</h1>
          </div>
          {sessionId && (
            <Button variant="outline" size="sm" onClick={handleReset}>
              <Trash2 className="h-4 w-4 mr-2" />
              Start Over
            </Button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs
          value={activeStep}
          onValueChange={(v) => setActiveStep(v as WizardStep)}
          className="space-y-8"
        >
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload" className="gap-2">
              <Upload className="h-4 w-4" />
              <span className="hidden sm:inline">Upload</span>
            </TabsTrigger>
            <TabsTrigger
              value="metadata"
              disabled={!canProceedToMetadata}
              className="gap-2"
            >
              <FileText className="h-4 w-4" />
              <span className="hidden sm:inline">Metadata</span>
            </TabsTrigger>
            <TabsTrigger
              value="settings"
              disabled={!canProceedToSettings}
              className="gap-2"
            >
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
            <TabsTrigger
              value="download"
              disabled={!currentJob}
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              <span className="hidden sm:inline">Download</span>
            </TabsTrigger>
          </TabsList>

          {/* Upload Step */}
          <TabsContent value="upload" className="space-y-6">
            <FileDropzone />
            <FileList />
            {canProceedToMetadata && (
              <div className="flex justify-end">
                <Button onClick={() => setActiveStep("metadata")}>
                  Continue to Metadata
                </Button>
              </div>
            )}
          </TabsContent>

          {/* Metadata Step */}
          <TabsContent value="metadata" className="space-y-6">
            <MetadataEditor />
            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setActiveStep("upload")}>
                Back
              </Button>
              <Button
                onClick={() => setActiveStep("settings")}
                disabled={!canProceedToSettings}
              >
                Continue to Settings
              </Button>
            </div>
          </TabsContent>

          {/* Settings Step */}
          <TabsContent value="settings" className="space-y-6">
            <ConversionSettings />
            <div className="flex justify-between">
              <Button
                variant="outline"
                onClick={() => setActiveStep("metadata")}
              >
                Back
              </Button>
              <Button
                onClick={handleStartConversion}
                disabled={!canStartConversion || isConverting}
              >
                {isConverting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>Start Conversion</>
                )}
              </Button>
            </div>
          </TabsContent>

          {/* Download Step */}
          <TabsContent value="download" className="space-y-6">
            <ProgressTracker />
            {currentJob?.status === "completed" && (
              <div className="flex justify-center">
                <Button onClick={handleReset}>Convert More Files</Button>
              </div>
            )}
            {currentJob?.status === "failed" && (
              <div className="flex justify-center gap-4">
                <Button variant="outline" onClick={handleReset}>
                  Start Over
                </Button>
                <Button onClick={handleStartConversion}>Retry</Button>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
