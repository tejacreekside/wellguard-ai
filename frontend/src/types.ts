export type WellSummary = {
  well_id: string;
  api_number: string;
  operator_name: string;
  basin: string;
  formation: string;
  county: string;
  state: string;
  status: string;
  latitude: number | null;
  longitude: number | null;
  latest_oil_bbl: number;
  expected_oil_bbl: number;
  variance_pct: number;
  severity_score: number;
  risk_score: number;
  revenue_leakage_daily: number;
  recommendation_category: string;
  confidence_score: number;
  decline_model: string;
  model_r2: number;
  anomaly_types: string[];
  data_quality_score: number;
  flagged: boolean;
};

export type PortfolioSummary = {
  portfolio_health_score: number;
  well_count: number;
  active_well_count: number;
  flagged_well_count: number;
  total_daily_revenue_leakage: number;
  estimated_30_day_leakage: number;
  estimated_annual_leakage: number;
  portfolio_risk_score: number;
  production_stability_score: number;
  operator_efficiency_index: number;
  intervention_roi_potential: number;
  top_bleeding_wells: WellSummary[];
  risk_distribution: Record<string, number>;
};

export type ExecutiveSummary = {
  headline: string;
  portfolio_takeaways: string[];
  recommended_actions: string[];
  financial_impact: string;
  generated_by: string;
};

export type Recommendation = {
  well_id: string;
  priority: string;
  category: string;
  rationale: string;
  suggested_next_step: string;
  decision_support_notice: string;
  expected_recovery_bbl_month: number;
  estimated_roi: number;
  payback_days: number;
  confidence_score: number;
};

export type WellAnalysis = {
  well: WellSummary;
  history: Array<Record<string, string | number>>;
  forecast: Array<Record<string, string | number>>;
  diagnostics: Record<string, unknown>;
};

export type OperatorRisk = {
  operator_name: string;
  well_count: number;
  flagged_wells: number;
  daily_revenue_leakage: number;
  risk_score: number;
  efficiency_index: number;
};

export type BasinSummary = {
  basin: string;
  well_count: number;
  flagged_wells: number;
  daily_revenue_leakage: number;
  average_risk_score: number;
  production_stability_score: number;
};

export type AnomalyRecord = {
  well_id: string;
  anomaly_type: string;
  severity: number;
  production_date: string;
  explanation: string;
  confidence_score: number;
};

export type CopilotResponse = {
  answer: string;
  confidence_score: number;
  retrieved_context: string[];
  mode: string;
};
