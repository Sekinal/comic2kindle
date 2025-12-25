import { create } from "zustand";
import type {
  ConversionJob,
  FileInfo,
  MangaMetadata,
  OutputFormat,
} from "@/types";

interface ConversionState {
  // Session
  sessionId: string | null;
  files: FileInfo[];

  // Metadata
  metadata: MangaMetadata;
  namingPattern: string;
  outputFormat: OutputFormat;

  // Conversion
  selectedFileIds: string[];
  currentJob: ConversionJob | null;

  // Actions
  setSession: (sessionId: string, files: FileInfo[]) => void;
  clearSession: () => void;
  setMetadata: (metadata: Partial<MangaMetadata>) => void;
  setNamingPattern: (pattern: string) => void;
  setOutputFormat: (format: OutputFormat) => void;
  setSelectedFileIds: (ids: string[]) => void;
  toggleFileSelection: (id: string) => void;
  selectAllFiles: () => void;
  setCurrentJob: (job: ConversionJob | null) => void;
  reset: () => void;
}

const defaultMetadata: MangaMetadata = {
  title: "",
  author: "",
  series: "",
  series_index: 1,
  description: "",
  cover_url: null,
  tags: [],
};

export const useConversionStore = create<ConversionState>((set, get) => ({
  // Initial state
  sessionId: null,
  files: [],
  metadata: { ...defaultMetadata },
  namingPattern: "{series} - Chapter {index:03d}",
  outputFormat: "epub",
  selectedFileIds: [],
  currentJob: null,

  // Actions
  setSession: (sessionId, files) =>
    set({
      sessionId,
      files,
      selectedFileIds: files.map((f) => f.id),
    }),

  clearSession: () =>
    set({
      sessionId: null,
      files: [],
      selectedFileIds: [],
      currentJob: null,
    }),

  setMetadata: (partial) =>
    set((state) => ({
      metadata: { ...state.metadata, ...partial },
    })),

  setNamingPattern: (pattern) => set({ namingPattern: pattern }),

  setOutputFormat: (format) => set({ outputFormat: format }),

  setSelectedFileIds: (ids) => set({ selectedFileIds: ids }),

  toggleFileSelection: (id) =>
    set((state) => ({
      selectedFileIds: state.selectedFileIds.includes(id)
        ? state.selectedFileIds.filter((fid) => fid !== id)
        : [...state.selectedFileIds, id],
    })),

  selectAllFiles: () =>
    set((state) => ({
      selectedFileIds: state.files.map((f) => f.id),
    })),

  setCurrentJob: (job) => set({ currentJob: job }),

  reset: () =>
    set({
      sessionId: null,
      files: [],
      metadata: { ...defaultMetadata },
      namingPattern: "{series} - Chapter {index:03d}",
      outputFormat: "epub",
      selectedFileIds: [],
      currentJob: null,
    }),
}));
