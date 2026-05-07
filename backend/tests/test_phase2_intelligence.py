import pandas as pd

from app.agents.workflow import WellGuardWorkflow
from app.models.schemas import DataQualityReport
from app.services.analysis_service import AnalysisService
from app.services.copilot_service import CopilotService


def phase2_well_df():
    rows = []
    for month in range(18):
        oil = 1200 - month * 22
        water = 120 + month * 8
        if month >= 15:
            oil *= 0.45
            water *= 2.4
        rows.append(
            {
                "well_id": "OK-REAL-1",
                "api_number": "3505123456",
                "operator_name": "Kirkpatrick Oil",
                "basin": "STACK",
                "formation": "Meramec",
                "county": "Kingfisher",
                "state": "OK",
                "production_date": pd.Timestamp("2024-01-01") + pd.DateOffset(months=month),
                "oil_bbl": oil,
                "gas_mcf": oil * 2.2,
                "water_bbl": water,
                "status": "active",
                "latitude": 35.8,
                "longitude": -97.9,
            }
        )
    return pd.DataFrame(rows)


def test_anomaly_detection_and_auto_model_metadata():
    analysis = AnalysisService().well_analysis(phase2_well_df())
    assert analysis.well.decline_model in {"hyperbolic", "exponential", "harmonic", "fallback"}
    assert analysis.well.anomaly_types
    assert analysis.diagnostics["rolling_trend"]


def test_agent_orchestration_returns_expanded_outputs():
    service = AnalysisService()
    summaries = service.analyze_portfolio(phase2_well_df())
    portfolio = service.portfolio_summary(summaries)
    result = WellGuardWorkflow().orchestrate(
        portfolio,
        summaries,
        service.basin_summaries(summaries),
        service.operator_risk(summaries),
        DataQualityReport(score=92, rows_received=18, rows_loaded=18),
    )
    assert result["portfolio"]["portfolio_risk_score"] >= 0
    assert result["data_quality"]["data_quality_score"] == 92


def test_copilot_retrieves_high_risk_context():
    service = AnalysisService()
    summaries = service.analyze_portfolio(phase2_well_df())
    recs = WellGuardWorkflow().recommendations(summaries)
    answer = CopilotService().query("Which wells are highest risk in STACK basin?", summaries, recs)
    assert "OK-REAL-1" in answer.answer
    assert answer.confidence_score > 0
