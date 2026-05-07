from app.agents.base import Agent
from app.models.schemas import WellAnalysis


class DeclineForecastAgent(Agent[WellAnalysis, dict[str, object]]):
    name = "DeclineForecastAgent"

    def run(self, payload: WellAnalysis) -> dict[str, object]:
        diagnostics = payload.diagnostics
        return {
            "well_id": payload.well.well_id,
            "confidence_score": diagnostics["confidence_score"],
            "three_month_loss_bbl": diagnostics["future_loss_3_month_bbl"],
            "six_month_loss_bbl": diagnostics["future_loss_6_month_bbl"],
            "twelve_month_loss_bbl": diagnostics["future_loss_12_month_bbl"],
            "forecast_note": "Forecast uses Arps decline with confidence adjusted for data quality, fit, and production consistency.",
        }
