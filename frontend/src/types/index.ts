/** Output format options for conversion */
export type OutputFormat = "epub" | "mobi" | "both";

/** Status of a conversion job */
export type ConversionStatus =
  | "pending"
  | "extracting"
  | "converting"
  | "completed"
  | "failed";

/** Information about an uploaded file */
export interface FileInfo {
  id: string;
  original_name: string;
  size: number;
  page_count: number;
  extension: string;
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
  series_index: number;
  description: string;
  cover_url: string | null;
  tags: string[];
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
}

/** A conversion job */
export interface ConversionJob {
  job_id: string;
  session_id: string;
  status: ConversionStatus;
  progress: number;
  current_file: string | null;
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
