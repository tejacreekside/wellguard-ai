from app.agents.intervention_advisor import InterventionAdvisorAgent
from app.models.schemas import WellSummary


def make_summary(category: str) -> WellSummary:
    return WellSummary(
        well_id="OK-1001",
        operator_name="Mewbourne Oil",
        basin="SCOOP",
        formation="Woodford",
        status="active",
        latest_oil_bbl=500,
        expected_oil_bbl=900,
        variance_pct=0.44,
        severity_score=75,
        risk_score=80,
        revenue_leakage_daily=920,
        recommendation_category=category,
        confidence_score=82,
        flagged=True,
    )


def test_recommendation_contains_decision_support_notice():
    recs = InterventionAdvisorAgent().run([make_summary("workover candidate")])
    assert recs[0].priority == "Critical"
    assert "Decision-support only" in recs[0].decision_support_notice
    assert "mechanical" in recs[0].suggested_next_step
