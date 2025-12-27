import type {
  Capabilities,
  ConversionJob,
  ConversionRequest,
  DeviceProfile,
  DownloadInfo,
  FileInfo,
  FilenameParseResult,
  MetadataSearchResult,
  UploadResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Request failed");
  }
  return response.json();
}

/** Upload files to create a new session */
export async function uploadFiles(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<UploadResponse>(response);
}

/** Get files in a session */
export async function getSessionFiles(sessionId: string): Promise<FileInfo[]> {
  const response = await fetch(`${API_BASE}/upload/${sessionId}`);
  return handleResponse<FileInfo[]>(response);
}

/** Delete a session and its files */
export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/upload/${sessionId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new ApiError(response.status, "Failed to delete session");
  }
}

/** Delete a single file from a session */
export async function deleteFile(
  sessionId: string,
  fileId: string
): Promise<void> {
  const response = await fetch(`${API_BASE}/upload/${sessionId}/${fileId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new ApiError(response.status, "Failed to delete file");
  }
}

/** Update file order for merging */
export async function updateFileOrder(
  sessionId: string,
  fileOrder: string[]
): Promise<FileInfo[]> {
  const response = await fetch(`${API_BASE}/upload/${sessionId}/order`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_order: fileOrder }),
  });
  return handleResponse<FileInfo[]>(response);
}

/** Get file preview URL */
export function getFilePreviewUrl(sessionId: string, fileId: string): string {
  return `${API_BASE}/upload/${sessionId}/${fileId}/preview`;
}

/** Parse filename to extract metadata */
export async function parseFilename(
  sessionId: string,
  fileId: string
): Promise<FilenameParseResult> {
  const response = await fetch(`${API_BASE}/upload/${sessionId}/${fileId}/parse`);
  return handleResponse<FilenameParseResult>(response);
}

/** Get suggested file order based on filenames */
export async function suggestFileOrder(sessionId: string): Promise<string[]> {
  const response = await fetch(`${API_BASE}/upload/${sessionId}/suggest-order`, {
    method: "POST",
  });
  return handleResponse<string[]>(response);
}

/** Search for manga metadata */
export async function searchMetadata(
  query: string,
  limit = 10
): Promise<MetadataSearchResult[]> {
  const response = await fetch(`${API_BASE}/metadata/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });

  return handleResponse<MetadataSearchResult[]>(response);
}

/** Get cover image URL (proxied) */
export function getCoverImageUrl(url: string): string {
  return `${API_BASE}/metadata/cover?url=${encodeURIComponent(url)}`;
}

/** Start a conversion job */
export async function startConversion(
  request: ConversionRequest
): Promise<ConversionJob> {
  const response = await fetch(`${API_BASE}/convert`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  return handleResponse<ConversionJob>(response);
}

/** Get conversion job status */
export async function getJobStatus(jobId: string): Promise<ConversionJob> {
  const response = await fetch(`${API_BASE}/convert/${jobId}/status`);
  return handleResponse<ConversionJob>(response);
}

/** List downloads for a session */
export async function listDownloads(sessionId: string): Promise<DownloadInfo[]> {
  const response = await fetch(`${API_BASE}/download/${sessionId}`);
  return handleResponse<DownloadInfo[]>(response);
}

/** Get download URL for a file */
export function getDownloadUrl(sessionId: string, filename: string): string {
  return `${API_BASE}/download/${sessionId}/${encodeURIComponent(filename)}`;
}

/** Get download URL for all files as ZIP */
export function getAllDownloadsUrl(sessionId: string): string {
  return `${API_BASE}/download/${sessionId}/all`;
}

/** Get all available device profiles */
export async function getDevices(): Promise<DeviceProfile[]> {
  const response = await fetch(`${API_BASE}/devices`);
  return handleResponse<DeviceProfile[]>(response);
}

/** Get a specific device profile */
export async function getDevice(profileId: string): Promise<DeviceProfile> {
  const response = await fetch(`${API_BASE}/devices/${profileId}`);
  return handleResponse<DeviceProfile>(response);
}

/** Get system capabilities (AI upscaling, supported formats) */
export async function getCapabilities(): Promise<Capabilities> {
  const response = await fetch(`${API_BASE}/devices/capabilities`);
  return handleResponse<Capabilities>(response);
}

/**
 * Batched initialization data - fetches devices and capabilities in parallel.
 * Use this instead of separate getDevices() and getCapabilities() calls
 * to reduce API round-trips during initial page load.
 */
export interface InitialData {
  devices: DeviceProfile[];
  capabilities: Capabilities;
}

// Cache for initialization data (devices and capabilities are static)
let cachedInitialData: InitialData | null = null;
let initialDataPromise: Promise<InitialData> | null = null;

export async function getInitialData(): Promise<InitialData> {
  // Return cached data if available
  if (cachedInitialData) {
    return cachedInitialData;
  }

  // Deduplicate in-flight requests
  if (initialDataPromise) {
    return initialDataPromise;
  }

  // Fetch both in parallel
  initialDataPromise = Promise.all([
    getDevices(),
    getCapabilities(),
  ]).then(([devices, capabilities]) => {
    cachedInitialData = { devices, capabilities };
    initialDataPromise = null;
    return cachedInitialData;
  }).catch((error) => {
    initialDataPromise = null;
    throw error;
  });

  return initialDataPromise;
}

/** Clear cached initialization data (useful for testing or refresh) */
export function clearInitialDataCache(): void {
  cachedInitialData = null;
  initialDataPromise = null;
}

export { ApiError };
