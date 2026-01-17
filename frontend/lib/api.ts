import type {
  AnalyzeRequest,
  Colony,
  Plate,
  PlateAttributes,
  UploadResponse
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function check<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }
  return response.json() as Promise<T>;
}

async function fetchWithRetry(input: RequestInfo, init: RequestInit, retryMs = 600) {
  try {
    return await fetch(input, init);
  } catch (err) {
    await new Promise((resolve) => setTimeout(resolve, retryMs));
    return fetch(input, init);
  }
}

export async function uploadImages(files: File[], metadata?: Record<string, string>) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  if (metadata && Object.keys(metadata).length > 0) {
    formData.append("metadata", JSON.stringify(metadata));
  }
  const response = await fetchWithRetry(`${API_BASE}/upload`, {
    method: "POST",
    body: formData
  });
  return check<UploadResponse>(response);
}

export async function analyzePlates(request: AnalyzeRequest) {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
  return check<{ analyzed: string[] }>(response);
}

export async function getPlates() {
  const response = await fetch(`${API_BASE}/plates`, { cache: "no-store" });
  return check<Plate[]>(response);
}

export async function getPlate(plateId: string) {
  const response = await fetch(`${API_BASE}/plate/${plateId}`, { cache: "no-store" });
  return check<Plate>(response);
}

export async function getPlateColonies(plateId: string) {
  const response = await fetch(`${API_BASE}/plate/${plateId}/colonies`, {
    cache: "no-store"
  });
  return check<Colony[]>(response);
}

export async function updatePlateAttributes(plateId: string, attributes: PlateAttributes) {
  const response = await fetch(`${API_BASE}/plate/${plateId}/attributes`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(attributes)
  });
  return check<Plate>(response);
}

export async function deletePlate(plateId: string) {
  const response = await fetch(`${API_BASE}/plate/${plateId}`, {
    method: "DELETE"
  });
  return check<{ deleted: string }>(response);
}

export function getExportUrl(plateId: string) {
  return `${API_BASE}/export/plate/${plateId}/colonies.csv`;
}

export function getReportUrl(plateId: string, format: "pdf" | "md") {
  return `${API_BASE}/report/plate/${plateId}?format=${format}`;
}

export function resolveApiUrl(path?: string | null) {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_BASE}${path}`;
}
