from app.agents.base import Agent
from app.models.schemas import Recommendation, WellSummary


NOTICE = "Decision-support only. Recommendations are not engineering approval and require qualified operational review."


class InterventionAdvisorAgent(Agent[list[WellSummary], list[Recommendation]]):
    name = "InterventionAdvisorAgent"

    def run(self, payload: list[WellSummary]) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        for well in sorted(payload, key=lambda x: x.risk_score, reverse=True):
            if not well.flagged and well.risk_score < 35:
                continue
            priority = "Critical" if well.risk_score >= 75 else "High" if well.risk_score >= 55 else "Watch"
            recommendations.append(
                Recommendation(
                    well_id=well.well_id,
                    priority=priority,
                    category=well.recommendation_category,
                    rationale=self._rationale(well),
                    suggested_next_step=self._next_step(well.recommendation_category),
                    decision_support_notice=NOTICE,
                )
            )
        return recommendations

    def _rationale(self, well: WellSummary) -> str:
        gap = round(well.variance_pct * 100, 1)
        return (
            f"{well.well_id} is {gap}% below expected production with "
            f"${well.revenue_leakage_daily:,.0f}/day estimated leakage and risk score {well.risk_score}."
        )

    def _next_step(self, category: str) -> str:
        steps = {
            "artificial lift review": "Review lift performance, fluid level, pump runtime, and water handling constraints.",
            "workover candidate": "Validate the sudden production break and screen for mechanical integrity or near-wellbore issues.",
            "chemical treatment review": "Check paraffin, scale, corrosion, and recent treatment history before scheduling field action.",
            "shut-in / inactive review": "Confirm operational status, downtime reason, restart economics, and regulatory constraints.",
            "data quality review": "Reconcile production allocation, missing months, meter anomalies, and duplicate reports.",
            "normal decline / no action": "Continue routine surveillance and refresh model after the next production cycle.",
        }
        return steps.get(category, "Review well file, recent operations, and production allocation before intervention.")
