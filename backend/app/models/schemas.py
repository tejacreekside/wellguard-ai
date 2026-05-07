from datetime import date
from typing import Any

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


class UploadResponse(BaseModel):
    rows_ingested: int
    wells_loaded: int
    warnings: list[str] = Field(default_factory=list)


class ProductionRecord(BaseModel):
    well_id: str
    operator_name: str
    basin: str
    formation: str
    production_date: date
    oil_bbl: float
    gas_mcf: float
    water_bbl: float
    status: str


class WellSummary(BaseModel):
    well_id: str
    operator_name: str
    basin: str
    formation: str
    status: str
    latest_oil_bbl: float
    expected_oil_bbl: float
    variance_pct: float
    severity_score: float
    risk_score: float
    revenue_leakage_daily: float
    recommendation_category: str
    confidence_score: float
    flagged: bool


class PortfolioSummary(BaseModel):
    portfolio_health_score: float
    well_count: int
    active_well_count: int
    flagged_well_count: int
    total_daily_revenue_leakage: float
    estimated_30_day_leakage: float
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


class ExecutiveSummary(BaseModel):
    headline: str
    portfolio_takeaways: list[str]
    recommended_actions: list[str]
    financial_impact: str
    generated_by: str = "WellGuard AI deterministic executive agent"


class AnalysisRequest(BaseModel):
    oil_price: float = Field(default=70.0, gt=0, le=300)
    threshold: float = Field(default=0.15, gt=0, lt=0.9)
