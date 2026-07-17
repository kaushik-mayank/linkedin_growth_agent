import type {
  Memory,
  Project,
  ParsedExport,
  RunResult,
  Snapshot,
  Week,
  Post,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
  } catch (e) {
    throw new ApiError(
      `Can't reach the backend at ${API_BASE}. Is it running? (${String(e)})`,
      0
    );
  }

  if (!resp.ok) {
    let detail = `${resp.status} ${resp.statusText}`;
    try {
      const body = await resp.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      /* keep the status-line detail */
    }
    throw new ApiError(detail, resp.status);
  }

  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const api = {
  base: API_BASE,

  // Projects
  listProjects: () => request<Project[]>("/projects"),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  createProject: (body: Partial<Project>) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(body) }),
  updateProject: (id: string, body: Partial<Project>) =>
    request<Project>(`/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteProject: (id: string) =>
    request<{ deleted: boolean }>(`/projects/${id}`, { method: "DELETE" }),

  // Analytics
  listSnapshots: (projectId: string) =>
    request<Snapshot[]>(`/projects/${projectId}/analytics/snapshots`),
  previewUpload: async (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const resp = await fetch(
      `${API_BASE}/projects/${projectId}/analytics/preview`,
      { method: "POST", body: form }
    );
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      throw new ApiError(body?.detail || "Parse failed", resp.status);
    }
    return (await resp.json()) as ParsedExport & { file_name: string };
  },
  confirmUpload: async (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const resp = await fetch(
      `${API_BASE}/projects/${projectId}/analytics/upload`,
      { method: "POST", body: form }
    );
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      throw new ApiError(body?.detail || "Upload failed", resp.status);
    }
    return (await resp.json()) as { snapshot: Snapshot; parsed: ParsedExport };
  },

  // Weeks
  listWeeks: (projectId: string) =>
    request<Week[]>(`/projects/${projectId}/weeks`),
  getWeek: (projectId: string, weekId: string) =>
    request<{ week: Week; posts: Post[] }>(
      `/projects/${projectId}/weeks/${weekId}`
    ),

  // Memory
  listMemory: (projectId: string) =>
    request<Memory[]>(`/projects/${projectId}/memory`),

  // Agent (non-streaming fallback)
  runWeekly: (projectId: string) =>
    request<RunResult>(`/projects/${projectId}/run-weekly`, {
      method: "POST",
      body: JSON.stringify({}),
    }),

  planDownloadUrl: (projectId: string, filename: string) =>
    `${API_BASE}/projects/${projectId}/plans/${filename}`,
};

export { ApiError };
