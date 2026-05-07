from app.agents.base import Agent
from app.models.schemas import ExecutiveSummary, PortfolioSummary, Recommendation


class ExecutiveSummaryAgent(Agent[tuple[PortfolioSummary, list[Recommendation]], ExecutiveSummary]):
    name = "ExecutiveSummaryAgent"

    def run(self, payload: tuple[PortfolioSummary, list[Recommendation]]) -> ExecutiveSummary:
        summary, recommendations = payload
        critical = [r for r in recommendations if r.priority == "Critical"]
        headline = (
            f"Portfolio health is {summary.portfolio_health_score}/100 with "
            f"${summary.total_daily_revenue_leakage:,.0f}/day in modeled preventable leakage."
        )
        takeaways = [
            f"{summary.flagged_well_count} of {summary.well_count} wells are flagged for abnormal decline or inactive risk.",
            f"Top 10 wells account for ${sum(w.revenue_leakage_daily for w in summary.top_bleeding_wells):,.0f}/day of estimated leakage.",
            f"Risk mix: {summary.risk_distribution['high']} high, {summary.risk_distribution['medium']} medium, {summary.risk_distribution['low']} low.",
        ]
        actions = [
            "Review critical wells in the next operations meeting and assign owner-level follow-up.",
            "Validate production allocation and downtime causes before approving field spend.",
            "Refresh analysis after the next production upload to measure recovered barrels and leakage reduction.",
        ]
        if critical:
            actions.insert(0, f"Prioritize {len(critical)} critical intervention candidates before lower-risk surveillance work.")
        return ExecutiveSummary(
            headline=headline,
            portfolio_takeaways=takeaways,
            recommended_actions=actions,
            financial_impact=f"Modeled 30-day exposure is ${summary.estimated_30_day_leakage:,.0f} at current oil price assumptions.",
        )
