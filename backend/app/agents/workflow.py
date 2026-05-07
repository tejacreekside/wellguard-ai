from app.agents.executive_summary import ExecutiveSummaryAgent
from app.agents.intervention_advisor import InterventionAdvisorAgent
from app.agents.production_monitoring import ProductionMonitoringAgent
from app.agents.revenue_agent import RevenueLeakageAgent
from app.models.schemas import ExecutiveSummary, PortfolioSummary, Recommendation, WellSummary


class WellGuardWorkflow:
    def __init__(self) -> None:
        self.monitor = ProductionMonitoringAgent()
        self.revenue = RevenueLeakageAgent()
        self.intervention = InterventionAdvisorAgent()
        self.executive = ExecutiveSummaryAgent()

    def recommendations(self, wells: list[WellSummary]) -> list[Recommendation]:
        return self.intervention.run(wells)

    def executive_summary(self, portfolio: PortfolioSummary, wells: list[WellSummary]) -> ExecutiveSummary:
        recs = self.recommendations(wells)
        return self.executive.run((portfolio, recs))

    def telemetry(self, wells: list[WellSummary]) -> dict[str, object]:
        return {
            "monitoring": self.monitor.run(wells),
            "revenue": self.revenue.run(wells),
        }


workflow = WellGuardWorkflow()
