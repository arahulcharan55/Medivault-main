const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

export type ApiError = { error: { code: string; message: string; request_id?: string } };

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("medivault_token");
}

export function setToken(token: string) {
  localStorage.setItem("medivault_token", token);
}

export function clearToken() {
  localStorage.removeItem("medivault_token");
  localStorage.removeItem("medivault_profile");
}

export function getProfile<T>(): T | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("medivault_profile");
  return raw ? (JSON.parse(raw) as T) : null;
}

export function setProfile(profile: unknown) {
  localStorage.setItem("medivault_profile", JSON.stringify(profile));
}

function errorMessage(body: unknown, fallback: string) {
  if (!body || typeof body !== "object") return fallback;
  const rec = body as Record<string, unknown>;
  const err = rec.error as Record<string, unknown> | undefined;
  if (err && typeof err.message === "string") return err.message;
  const detail = rec.detail as Record<string, unknown> | string | undefined;
  if (detail && typeof detail === "object" && typeof detail.message === "string") return detail.message;
  if (typeof detail === "string") return detail;
  return fallback;
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(errorMessage(body, res.statusText || "Request failed"));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function uploadDocument(file: File) {
  const form = new FormData();
  form.append("file", file);
  return api<DocumentItem>("/documents/upload", { method: "POST", body: form });
}

export type UserProfile = {
  user_id: string;
  email: string;
  role: "patient" | "doctor";
  patient_id?: string;
  doctor_id?: string;
  name?: string;
};

export type DocumentItem = {
  id: string;
  filename: string;
  mime_type: string;
  file_size: number;
  processing_status: string;
  document_date?: string | null;
  uploaded_at: string;
};

export type TimelineItem = {
  type: string;
  id: string;
  display_name: string;
  value?: string | null;
  unit?: string | null;
  interpretation?: string | null;
  effective_time?: string | null;
  document_id?: string | null;
};

export type ConsentItem = {
  id: string;
  patient_id: string;
  doctor_id: string;
  doctor_name?: string | null;
  scope: Record<string, unknown>;
  permissions: string[];
  issued_at: string;
  expires_at: string;
  revoked_at?: string | null;
  status: string;
};

export type AuditItem = {
  id: string;
  action: string;
  outcome: string;
  timestamp: string;
  actor_role: string;
  resource_type?: string | null;
};

export type DoctorOption = { id: string; name: string; specialization?: string | null; organization?: string | null };

export type HealthSummary = {
  counts: {
    documents: number;
    observations: number;
    medications: number;
    conditions: number;
    procedures: number;
    allergies: number;
  };
  latest_observations: Array<{
    id: string;
    display_name: string;
    value: string;
    unit?: string | null;
    interpretation?: string | null;
    effective_time?: string | null;
  }>;
  medications: Array<{ id: string; medication_name: string; dosage?: string | null; frequency?: string | null }>;
  conditions: Array<{ id: string; display_name: string; onset_date?: string | null }>;
  allergies: Array<{ id: string; substance: string; reaction?: string | null }>;
  abnormal_observations: Array<{
    id: string;
    display_name: string;
    value: string;
    unit?: string | null;
    interpretation?: string | null;
  }>;
  processing: { pending: number; failed: number; validated: number };
};

export type ExtractionJob = {
  id: string;
  document_id: string;
  status: string;
  extracted_json?: Record<string, unknown> | null;
  raw_ocr_text?: string | null;
  error_message?: string | null;
};

export const RECORD_TYPES = [
  { id: "observations", label: "Labs & vitals" },
  { id: "medications", label: "Medications" },
  { id: "conditions", label: "Conditions" },
  { id: "procedures", label: "Procedures" },
  { id: "allergies", label: "Allergies" },
] as const;
