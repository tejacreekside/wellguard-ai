from app.agents.base import Agent
from app.models.schemas import PortfolioSummary


class PortfolioRiskAgent(Agent[PortfolioSummary, dict[str, object]]):
    name = "PortfolioRiskAgent"

    def run(self, payload: PortfolioSummary) -> dict[str, object]:
        self.log("portfolio_risk_scored")
        posture = "elevated" if payload.portfolio_risk_score >= 45 else "controlled"
        return {
            "confidence_score": 86,
            "portfolio_risk_score": payload.portfolio_risk_score,
            "risk_posture": posture,
            "annual_leakage": payload.estimated_annual_leakage,
            "summary": f"Portfolio risk is {posture} with annualized leakage exposure of ${payload.estimated_annual_leakage:,.0f}.",
        }
