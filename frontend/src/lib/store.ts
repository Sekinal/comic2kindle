import { create } from "zustand";
import type {
  ChapterInfo,
  ConversionJob,
  DeviceProfileId,
  EpubExtractionMode,
  FileInfo,
  ImageProcessingOptions,
  MangaMetadata,
  OutputFormat,
  UpscaleMethod,
} from "@/types";

/** View mode for the conversion page */
export type ViewMode = "wizard" | "quick";

interface ConversionState {
  // Session
  sessionId: string | null;
  files: FileInfo[];

  // Metadata
  metadata: MangaMetadata;
  namingPattern: string;
  outputFormat: OutputFormat;

  // Merge/Split settings
  mergeFiles: boolean;
  fileOrder: string[];
  epubMode: EpubExtractionMode;
  maxOutputSizeMb: number;

  // Image processing
  imageOptions: ImageProcessingOptions;

  // View mode
  viewMode: ViewMode;

  // Conversion
  selectedFileIds: string[];
  currentJob: ConversionJob | null;

  // Computed
  hasEpubFiles: () => boolean;
  estimatedTotalSize: () => number;

  // Actions
  setSession: (sessionId: string, files: FileInfo[]) => void;
  clearSession: () => void;
  setFiles: (files: FileInfo[]) => void;
  removeFile: (fileId: string) => void;
  setMetadata: (metadata: Partial<MangaMetadata>) => void;
  setChapterInfo: (chapterInfo: Partial<ChapterInfo>) => void;
  setNamingPattern: (pattern: string) => void;
  setOutputFormat: (format: OutputFormat) => void;
  setSelectedFileIds: (ids: string[]) => void;
  toggleFileSelection: (id: string) => void;
  selectAllFiles: () => void;
  setCurrentJob: (job: ConversionJob | null) => void;
  setMergeFiles: (merge: boolean) => void;
  setFileOrder: (order: string[]) => void;
  reorderFile: (fromIndex: number, toIndex: number) => void;
  setEpubMode: (mode: EpubExtractionMode) => void;
  setMaxOutputSizeMb: (size: number) => void;
  setImageOptions: (options: Partial<ImageProcessingOptions>) => void;
  setDeviceProfile: (profile: DeviceProfileId) => void;
  setUpscaleMethod: (method: UpscaleMethod) => void;
  setViewMode: (mode: ViewMode) => void;
  reset: () => void;
}

const defaultChapterInfo: ChapterInfo = {
  chapter_start: null,
  chapter_end: null,
  volume: null,
  title_prefix: "",
  title_suffix: "",
};

const defaultMetadata: MangaMetadata = {
  title: "",
  author: "",
  series: "",
  chapter_info: { ...defaultChapterInfo },
  description: "",
  cover_url: null,
  tags: [],
  title_format: "{series} - Ch. {chapter}",
};

const defaultImageOptions: ImageProcessingOptions = {
  device_profile: "kindle_paperwhite_5",
  custom_width: null,
  custom_height: null,
  upscale_method: "lanczos",
  detect_spreads: true,
  rotate_spreads: true,
  fill_screen: true,
};

export const useConversionStore = create<ConversionState>((set, get) => ({
  // Initial state
  sessionId: null,
  files: [],
  metadata: { ...defaultMetadata },
  namingPattern: "{series} - Ch. {chapter}",
  outputFormat: "epub",
  mergeFiles: false,
  fileOrder: [],
  epubMode: "images_only",
  maxOutputSizeMb: 200,
  imageOptions: { ...defaultImageOptions },
  viewMode: "wizard",
  selectedFileIds: [],
  currentJob: null,

  // Computed
  hasEpubFiles: () => get().files.some((f) => f.input_format === "epub"),

  estimatedTotalSize: () => {
    const state = get();
    const selectedFiles = state.files.filter((f) =>
      state.selectedFileIds.includes(f.id)
    );
    return selectedFiles.reduce((sum, f) => sum + f.estimated_output_size, 0);
  },

  // Actions
  setSession: (sessionId, files) => {
    const fileOrder = files.map((f) => f.id);
    set({
      sessionId,
      files,
      selectedFileIds: fileOrder,
      fileOrder,
    });
  },

  clearSession: () =>
    set({
      sessionId: null,
      files: [],
      selectedFileIds: [],
      fileOrder: [],
      currentJob: null,
    }),

  setFiles: (files) => set({ files }),

  removeFile: (fileId) =>
    set((state) => ({
      files: state.files.filter((f) => f.id !== fileId),
      selectedFileIds: state.selectedFileIds.filter((id) => id !== fileId),
      fileOrder: state.fileOrder.filter((id) => id !== fileId),
    })),

  setMetadata: (partial) =>
    set((state) => ({
      metadata: { ...state.metadata, ...partial },
    })),

  setChapterInfo: (partial) =>
    set((state) => ({
      metadata: {
        ...state.metadata,
        chapter_info: { ...state.metadata.chapter_info, ...partial },
      },
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

  setMergeFiles: (merge) => set({ mergeFiles: merge }),

  setFileOrder: (order) => set({ fileOrder: order }),

  reorderFile: (fromIndex, toIndex) =>
    set((state) => {
      const newOrder = [...state.fileOrder];
      const [removed] = newOrder.splice(fromIndex, 1);
      newOrder.splice(toIndex, 0, removed);
      return { fileOrder: newOrder };
    }),

  setEpubMode: (mode) => set({ epubMode: mode }),

  setMaxOutputSizeMb: (size) => set({ maxOutputSizeMb: size }),

  setImageOptions: (options) =>
    set((state) => ({
      imageOptions: { ...state.imageOptions, ...options },
    })),

  setDeviceProfile: (profile) =>
    set((state) => ({
      imageOptions: { ...state.imageOptions, device_profile: profile },
    })),

  setUpscaleMethod: (method) =>
    set((state) => ({
      imageOptions: { ...state.imageOptions, upscale_method: method },
    })),

  setViewMode: (mode) => set({ viewMode: mode }),

  reset: () =>
    set({
      sessionId: null,
      files: [],
      metadata: { ...defaultMetadata },
      namingPattern: "{series} - Ch. {chapter}",
      outputFormat: "epub",
      mergeFiles: false,
      fileOrder: [],
      epubMode: "images_only",
      maxOutputSizeMb: 200,
      imageOptions: { ...defaultImageOptions },
      viewMode: "wizard",
      selectedFileIds: [],
      currentJob: null,
    }),
}));
