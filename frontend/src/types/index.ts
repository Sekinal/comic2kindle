/** Output format options for conversion */
export type OutputFormat = "epub" | "mobi" | "both";

/** Input format types */
export type InputFormat = "cbz" | "cbr" | "epub" | "zip" | "rar" | "images";

/** EPUB extraction mode */
export type EpubExtractionMode = "images_only" | "preserve";

/** Status of a conversion job */
export type ConversionStatus =
  | "pending"
  | "extracting"
  | "processing"
  | "merging"
  | "converting"
  | "splitting"
  | "completed"
  | "failed";

/** Target e-reader device profiles */
export type DeviceProfileId =
  | "kindle_basic"
  | "kindle_paperwhite_5"
  | "kindle_scribe"
  | "kobo_clara_2e"
  | "kobo_libra_2"
  | "kobo_sage"
  | "custom";

/** Image upscaling method */
export type UpscaleMethod = "none" | "lanczos" | "ai_esrgan";

/** Reading direction for the ebook */
export type ReadingDirection = "rtl" | "ltr";

/** Chapter information for flexible metadata */
export interface ChapterInfo {
  chapter_start: number | null;
  chapter_end: number | null;
  volume: number | null;
  title_prefix: string;
  title_suffix: string;
}

/** Image processing options for conversion */
export interface ImageProcessingOptions {
  device_profile: DeviceProfileId;
  custom_width: number | null;
  custom_height: number | null;
  upscale_method: UpscaleMethod;
  detect_spreads: boolean;
  rotate_spreads: boolean;
  fill_screen: boolean;
  reading_direction: ReadingDirection;
}

/** Device profile information */
export interface DeviceProfile {
  id: DeviceProfileId;
  name: string;
  display_name: string;
  manufacturer: "kindle" | "kobo" | "custom";
  width: number;
  height: number;
  dpi: number;
  supports_color: boolean;
  recommended_format: string;
}

/** System capabilities */
export interface Capabilities {
  ai_upscaling_available: boolean;
  supported_input_formats: string[];
  supported_output_formats: string[];
}

/** Information about an uploaded file */
export interface FileInfo {
  id: string;
  original_name: string;
  size: number;
  page_count: number;
  extension: string;
  input_format: InputFormat;
  preview_url: string | null;
  order: number;
  estimated_output_size: number;
  uploaded_at: string;
}

/** Response after file upload */
export interface UploadResponse {
  session_id: string;
  files: FileInfo[];
  message: string;
}

/** Metadata for a manga */
export interface MangaMetadata {
  title: string;
  author: string;
  series: string;
  chapter_info: ChapterInfo;
  description: string;
  cover_url: string | null;
  tags: string[];
  title_format: string;
}

/** Result from metadata search */
export interface MetadataSearchResult {
  id: string;
  title: string;
  author: string;
  description: string;
  cover_url: string | null;
  source: "mangadex" | "anilist";
}

/** Request to convert files */
export interface ConversionRequest {
  session_id: string;
  file_ids: string[];
  metadata: MangaMetadata;
  output_format: OutputFormat;
  naming_pattern: string;
  epub_mode: EpubExtractionMode;
  merge_files: boolean;
  file_order: string[];
  max_output_size_mb: number;
  image_options: ImageProcessingOptions;
}

/** A conversion job */
export interface ConversionJob {
  job_id: string;
  session_id: string;
  status: ConversionStatus;
  progress: number;
  current_file: string | null;
  current_phase: string;
  split_count: number;
  output_files: string[];
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

/** Download file info */
export interface DownloadInfo {
  filename: string;
  size: number;
  format: string;
  download_url: string;
}

/** Result of filename parsing */
export interface FilenameParseResult {
  series: string | null;
  chapter: number | null;
  volume: number | null;
  title: string | null;
}
