import type { AnomalyRecord, BasinSummary, CopilotResponse, ExecutiveSummary, OperatorRisk, PortfolioSummary, Recommendation, WellAnalysis, WellSummary } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "http://localhost:8000" : "/api");

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
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
    const response = await fetch(`${API_BASE}/upload-production-data`, { method: "POST", body: formData });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  },
};
