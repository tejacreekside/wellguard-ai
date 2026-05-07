export type WellSummary = {
  well_id: string;
  operator_name: string;
  basin: string;
  formation: string;
  status: string;
  latest_oil_bbl: number;
  expected_oil_bbl: number;
  variance_pct: number;
  severity_score: number;
  risk_score: number;
  revenue_leakage_daily: number;
  recommendation_category: string;
  confidence_score: number;
  flagged: boolean;
};

export type PortfolioSummary = {
  portfolio_health_score: number;
  well_count: number;
  active_well_count: number;
  flagged_well_count: number;
  total_daily_revenue_leakage: number;
  estimated_30_day_leakage: number;
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
};

export type WellAnalysis = {
  well: WellSummary;
  history: Array<Record<string, string | number>>;
  forecast: Array<Record<string, string | number>>;
  diagnostics: Record<string, unknown>;
};
