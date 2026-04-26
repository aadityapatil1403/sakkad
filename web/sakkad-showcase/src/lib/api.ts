import type {
  BackendCapture,
  GenerateResponse,
  GenerateImageResponse,
  HealthResponse,
  ApiError,
} from "./types";

function getBaseUrl(): string {
  return (
    (import.meta.env["VITE_BACKEND_URL"] as string | undefined) ??
    "http://127.0.0.1:8000"
  );
}

const BASE_HEADERS: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

async function apiFetch<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...BASE_HEADERS,
    ...(options.headers as Record<string, string>),
  };
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const err: ApiError = { message: `HTTP ${res.status}`, status: res.status };
    throw err;
  }
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>(`${getBaseUrl()}/api/health`);
}

export async function getGallery(): Promise<BackendCapture[]> {
  return apiFetch<BackendCapture[]>(`${getBaseUrl()}/api/gallery`);
}

export async function uploadCapture(
  file: File,
  sessionId?: string,
): Promise<BackendCapture> {
  const fd = new FormData();
  fd.append("file", file);
  if (sessionId) fd.append("session_id", sessionId);

  return apiFetch<BackendCapture>(`${getBaseUrl()}/api/capture`, {
    method: "POST",
    body: fd,
    // Do NOT set Content-Type — browser sets multipart boundary automatically
  });
}

export async function generateCopy(
  kind: GenerateResponse["kind"],
  source: { session_id?: string; capture_ids?: string[] },
): Promise<GenerateResponse> {
  return apiFetch<GenerateResponse>(`${getBaseUrl()}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kind, ...source }),
  });
}

export async function generateImage(
  statement: string,
  captureIds: string[],
): Promise<GenerateImageResponse> {
  return apiFetch<GenerateImageResponse>(`${getBaseUrl()}/api/generate/image`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ statement, capture_ids: captureIds }),
  });
}
