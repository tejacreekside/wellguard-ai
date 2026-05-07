from app.agents.base import Agent
from app.models.schemas import WellSummary


class ForecastValidationAgent(Agent[list[WellSummary], dict[str, object]]):
    name = "ForecastValidationAgent"

    def run(self, payload: list[WellSummary]) -> dict[str, object]:
        self.log("forecast_validation_completed")
        low_confidence = [well.well_id for well in payload if well.confidence_score < 55]
        return {
            "confidence_score": 78,
            "low_confidence_wells": low_confidence,
            "model_mix": self._model_mix(payload),
            "summary": f"{len(low_confidence)} wells need model validation due to low confidence or data instability.",
        }

    def _model_mix(self, wells: list[WellSummary]) -> dict[str, int]:
        output: dict[str, int] = {}
        for well in wells:
            output[well.decline_model] = output.get(well.decline_model, 0) + 1
        return output
