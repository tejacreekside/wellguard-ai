from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field


REQUIRED_COLUMNS = {
    "well_id",
    "operator_name",
    "basin",
    "formation",
    "production_date",
    "oil_bbl",
    "gas_mcf",
    "water_bbl",
    "status",
}

INTERNAL_COLUMNS = [
    "well_id",
    "api_number",
    "operator_name",
    "basin",
    "formation",
    "county",
    "state",
    "production_date",
    "oil_bbl",
    "gas_mcf",
    "water_bbl",
    "status",
    "latitude",
    "longitude",
]


class UploadResponse(BaseModel):
    rows_ingested: int
    wells_loaded: int
    warnings: list[str] = Field(default_factory=list)
    data_quality_score: float = 100.0
    source_type: str = "wellguard"


class ProductionRecord(BaseModel):
    well_id: str
    api_number: str = ""
    operator_name: str
    basin: str
    formation: str
    county: str = "Unknown"
    state: str = "OK"
    production_date: date
    oil_bbl: float
    gas_mcf: float
    water_bbl: float
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WellSummary(BaseModel):
    well_id: str
    api_number: str = ""
    operator_name: str
    basin: str
    formation: str
    county: str = "Unknown"
    state: str = "OK"
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    latest_oil_bbl: float
    expected_oil_bbl: float
    variance_pct: float
    severity_score: float
    risk_score: float
    revenue_leakage_daily: float
    recommendation_category: str
    confidence_score: float
    decline_model: str = "hyperbolic"
    model_r2: float = 0.0
    anomaly_types: list[str] = Field(default_factory=list)
    data_quality_score: float = 100.0
    flagged: bool


class PortfolioSummary(BaseModel):
    portfolio_health_score: float
    well_count: int
    active_well_count: int
    flagged_well_count: int
    total_daily_revenue_leakage: float
    estimated_30_day_leakage: float
    estimated_annual_leakage: float = 0.0
    portfolio_risk_score: float = 0.0
    production_stability_score: float = 0.0
    operator_efficiency_index: float = 0.0
    intervention_roi_potential: float = 0.0
    top_bleeding_wells: list[WellSummary]
    risk_distribution: dict[str, int]


class ForecastPoint(BaseModel):
    production_date: date
    expected_oil_bbl: float
    forecast_oil_bbl: float
    lower_oil_bbl: float
    upper_oil_bbl: float


class WellAnalysis(BaseModel):
    well: WellSummary
    history: list[dict[str, Any]]
    forecast: list[ForecastPoint]
    diagnostics: dict[str, Any]


class Recommendation(BaseModel):
    well_id: str
    priority: str
    category: str
    rationale: str
    suggested_next_step: str
    decision_support_notice: str
    expected_recovery_bbl_month: float = 0.0
    estimated_roi: float = 0.0
    payback_days: float = 0.0
    confidence_score: float = 70.0


class ExecutiveSummary(BaseModel):
    headline: str
    portfolio_takeaways: list[str]
    recommended_actions: list[str]
    financial_impact: str
    generated_by: str = "WellGuard AI deterministic executive agent"


class AnalysisRequest(BaseModel):
    oil_price: float = Field(default=70.0, gt=0, le=300)
    threshold: float = Field(default=0.15, gt=0, lt=0.9)


class DataQualityReport(BaseModel):
    score: float
    rows_received: int
    rows_loaded: int
    duplicate_rows: int = 0
    malformed_dates: int = 0
    clipped_negative_values: int = 0
    missing_required_values: int = 0
    warnings: list[str] = Field(default_factory=list)


class OperatorRisk(BaseModel):
    operator_name: str
    well_count: int
    flagged_wells: int
    daily_revenue_leakage: float
    risk_score: float
    efficiency_index: float


class BasinSummary(BaseModel):
    basin: str
    well_count: int
    flagged_wells: int
    daily_revenue_leakage: float
    average_risk_score: float
    production_stability_score: float


class AnomalyRecord(BaseModel):
    well_id: str
    anomaly_type: str
    severity: float
    production_date: date
    explanation: str
    confidence_score: float


class CopilotQuery(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class CopilotResponse(BaseModel):
    answer: str
    confidence_score: float
    retrieved_context: list[str] = Field(default_factory=list)
    mode: str = "deterministic-rag"
