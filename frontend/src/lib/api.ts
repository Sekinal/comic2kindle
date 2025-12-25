import type {
  ConversionJob,
  ConversionRequest,
  DownloadInfo,
  FileInfo,
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

export { ApiError };
