from app.agents.base import Agent
from app.models.schemas import WellSummary


class RevenueLeakageAgent(Agent[list[WellSummary], dict[str, object]]):
    name = "RevenueLeakageAgent"

    def run(self, payload: list[WellSummary]) -> dict[str, object]:
        leakage = sum(w.revenue_leakage_daily for w in payload)
        return {
            "daily_revenue_leakage": round(leakage, 2),
            "monthly_revenue_at_risk": round(leakage * 30, 2),
            "largest_sources": [w.well_id for w in sorted(payload, key=lambda x: x.revenue_leakage_daily, reverse=True)[:5]],
        }
