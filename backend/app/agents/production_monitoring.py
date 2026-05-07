from app.agents.base import Agent
from app.models.schemas import WellSummary


class ProductionMonitoringAgent(Agent[list[WellSummary], dict[str, object]]):
    name = "ProductionMonitoringAgent"

    def run(self, payload: list[WellSummary]) -> dict[str, object]:
        flagged = [w for w in payload if w.flagged]
        return {
            "flagged_wells": len(flagged),
            "high_risk_wells": [w.well_id for w in payload if w.risk_score >= 65],
            "monitoring_note": f"{len(flagged)} wells are producing materially below modeled decline expectations.",
        }
