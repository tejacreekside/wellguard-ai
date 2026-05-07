from __future__ import annotations

from app.agents.basin_benchmark import BasinBenchmarkAgent
from app.agents.data_quality import DataQualityAgent
from app.agents.executive_summary import ExecutiveSummaryAgent
from app.agents.forecast_validation import ForecastValidationAgent
from app.agents.intervention_advisor import InterventionAdvisorAgent
from app.agents.operator_comparison import OperatorComparisonAgent
from app.agents.portfolio_risk import PortfolioRiskAgent
from app.agents.production_monitoring import ProductionMonitoringAgent
from app.agents.revenue_agent import RevenueLeakageAgent
from app.models.schemas import BasinSummary, DataQualityReport, ExecutiveSummary, OperatorRisk, PortfolioSummary, Recommendation, WellSummary


class WellGuardWorkflow:
    def __init__(self) -> None:
        self.monitor = ProductionMonitoringAgent()
        self.revenue = RevenueLeakageAgent()
        self.intervention = InterventionAdvisorAgent()
        self.executive = ExecutiveSummaryAgent()
        self.basin = BasinBenchmarkAgent()
        self.portfolio_risk = PortfolioRiskAgent()
        self.data_quality = DataQualityAgent()
        self.forecast_validation = ForecastValidationAgent()
        self.operator_comparison = OperatorComparisonAgent()

    def recommendations(self, wells: list[WellSummary]) -> list[Recommendation]:
        return self.intervention.run(wells)

    def executive_summary(self, portfolio: PortfolioSummary, wells: list[WellSummary]) -> ExecutiveSummary:
        recs = self.recommendations(wells)
        return self.executive.run((portfolio, recs))

    def telemetry(self, wells: list[WellSummary]) -> dict[str, object]:
        return {
            "monitoring": self.monitor.run(wells),
            "revenue": self.revenue.run(wells),
            "forecast_validation": self.forecast_validation.run(wells),
        }

    def orchestrate(
        self,
        portfolio: PortfolioSummary,
        wells: list[WellSummary],
        basins: list[BasinSummary],
        operators: list[OperatorRisk],
        quality: DataQualityReport | None = None,
    ) -> dict[str, object]:
        return {
            "portfolio": self.portfolio_risk.run(portfolio),
            "monitoring": self.monitor.run(wells),
            "revenue": self.revenue.run(wells),
            "forecast_validation": self.forecast_validation.run(wells),
            "basin_benchmark": self.basin.run(basins),
            "operator_comparison": self.operator_comparison.run(operators),
            "data_quality": self.data_quality.run(quality) if quality else None,
            "recommendations": [item.model_dump() for item in self.recommendations(wells)],
        }


workflow = WellGuardWorkflow()
