from app.agents.base import Agent
from app.models.schemas import DataQualityReport


class DataQualityAgent(Agent[DataQualityReport, dict[str, object]]):
    name = "DataQualityAgent"

    def run(self, payload: DataQualityReport) -> dict[str, object]:
        self.log("data_quality_reviewed")
        grade = "high" if payload.score >= 85 else "moderate" if payload.score >= 65 else "low"
        return {
            "confidence_score": 90,
            "data_quality_score": payload.score,
            "quality_grade": grade,
            "warnings": payload.warnings,
            "summary": f"Dataset quality is {grade}; {payload.rows_loaded} of {payload.rows_received} rows loaded.",
        }
