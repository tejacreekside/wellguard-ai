from app.agents.base import Agent
from app.models.schemas import BasinSummary


class BasinBenchmarkAgent(Agent[list[BasinSummary], dict[str, object]]):
    name = "BasinBenchmarkAgent"

    def run(self, payload: list[BasinSummary]) -> dict[str, object]:
        self.log("basin_benchmark_started")
        if not payload:
            return {"confidence_score": 0, "summary": "No basin data available.", "basins": []}
        highest = max(payload, key=lambda item: item.daily_revenue_leakage)
        best = max(payload, key=lambda item: item.production_stability_score)
        return {
            "confidence_score": 82,
            "summary": f"{highest.basin} has the highest modeled leakage exposure; {best.basin} shows the strongest production stability.",
            "basins": [item.model_dump() for item in payload],
        }
