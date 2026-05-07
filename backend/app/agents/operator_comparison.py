from app.agents.base import Agent
from app.models.schemas import OperatorRisk


class OperatorComparisonAgent(Agent[list[OperatorRisk], dict[str, object]]):
    name = "OperatorComparisonAgent"

    def run(self, payload: list[OperatorRisk]) -> dict[str, object]:
        self.log("operator_comparison_completed")
        if not payload:
            return {"confidence_score": 0, "operators": [], "summary": "No operator data available."}
        worst = max(payload, key=lambda item: item.risk_score)
        best = max(payload, key=lambda item: item.efficiency_index)
        return {
            "confidence_score": 84,
            "operators": [item.model_dump() for item in payload],
            "summary": f"{worst.operator_name} has the highest risk exposure; {best.operator_name} has the strongest efficiency index.",
        }
