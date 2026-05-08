import type { AnomalyRecord, BasinSummary, CopilotResponse, ExecutiveSummary, OperatorRisk, PortfolioSummary, Recommendation, WellAnalysis, WellSummary } from "./types";

const REQUEST_TIMEOUT_MS = 15000;
const rawApiBase = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "http://localhost:8000" : "/api");
const API_BASE = normalizeApiBase(rawApiBase);

function normalizeApiBase(value: string) {
  const trimmed = value.trim().replace(/\/+$/, "");
  if (!trimmed || trimmed.includes("your-wellguard-api")) {
    return "/api";
  }
  return trimmed;
}

async function getJson<T>(path: string): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetchWithTimeout(url);
  if (!response.ok) {
    throw new Error(`API request failed (${response.status}) for ${url}: ${await responseError(response)}`);
  }
  return response.json();
}

async function fetchWithTimeout(url: string, options?: RequestInit) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(`API request timed out after ${REQUEST_TIMEOUT_MS / 1000}s for ${url}`);
    }
    throw err;
  } finally {
    window.clearTimeout(timeout);
  }
}

async function responseError(response: Response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const payload = await response.json().catch(() => null);
    if (payload?.detail) {
      return typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
    }
    return JSON.stringify(payload);
  }
  const text = await response.text();
  return text.trim().slice(0, 300) || response.statusText;
}

export const api = {
  portfolio: () => getJson<PortfolioSummary>("/portfolio/summary"),
  wells: () => getJson<WellSummary[]>("/wells"),
  recommendations: () => getJson<Recommendation[]>("/recommendations"),
  operators: () => getJson<OperatorRisk[]>("/operators"),
  basins: () => getJson<BasinSummary[]>("/basins"),
  anomalies: () => getJson<AnomalyRecord[]>("/anomalies"),
  executive: () => getJson<ExecutiveSummary>("/executive-summary"),
  executiveReportUrl: () => `${API_BASE}/executive/report`,
  wellAnalysis: (wellId: string) => getJson<WellAnalysis>(`/wells/${wellId}/analysis`),
  copilot: (question: string) => getJson<CopilotResponse>(`/copilot/query?q=${encodeURIComponent(question)}`),
  reportUrl: () => `${API_BASE}/reports/intervention-report.csv`,
  upload: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const url = `${API_BASE}/upload-production-data`;
    const response = await fetchWithTimeout(url, { method: "POST", body: formData });
    if (!response.ok) {
      throw new Error(`API request failed (${response.status}) for ${url}: ${await responseError(response)}`);
    }
    return response.json();
  },
};
