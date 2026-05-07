from __future__ import annotations

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.schemas import CopilotResponse, Recommendation, WellSummary


class CopilotService:
    """Deterministic RAG-style copilot using local TF-IDF retrieval."""

    def build_context(self, wells: list[WellSummary], recommendations: list[Recommendation]) -> list[str]:
        docs: list[str] = []
        for well in wells:
            docs.append(
                f"Well {well.well_id} operator {well.operator_name} basin {well.basin} formation {well.formation} "
                f"risk {well.risk_score} leakage {well.revenue_leakage_daily} flagged {well.flagged} "
                f"model {well.decline_model} anomalies {', '.join(well.anomaly_types)} category {well.recommendation_category}."
            )
        for rec in recommendations:
            docs.append(
                f"Recommendation for {rec.well_id}: {rec.priority} {rec.category}. {rec.rationale} "
                f"Next step: {rec.suggested_next_step} ROI {rec.estimated_roi} payback {rec.payback_days} days."
            )
        return docs

    def query(self, question: str, wells: list[WellSummary], recommendations: list[Recommendation]) -> CopilotResponse:
        docs = self.build_context(wells, recommendations)
        if not docs:
            return CopilotResponse(answer="No production intelligence context is currently loaded.", confidence_score=0, retrieved_context=[])
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(docs + [question])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
        top_idx = scores.argsort()[::-1][:5]
        context = [docs[i] for i in top_idx if scores[i] > 0]
        answer = self._deterministic_answer(question, wells, recommendations, context)
        confidence = round(float(max(scores[top_idx[0]] if len(top_idx) else 0, 0.35) * 100), 1)
        return CopilotResponse(answer=answer, confidence_score=min(confidence, 92), retrieved_context=context)

    def _deterministic_answer(self, question: str, wells: list[WellSummary], recommendations: list[Recommendation], context: list[str]) -> str:
        q = question.lower()
        basin_match = re.search(r"\b(scoop|stack|anadarko)\b", q)
        scoped = [w for w in wells if not basin_match or w.basin.lower() == basin_match.group(1)]
        if "highest risk" in q or "high risk" in q:
            top = sorted(scoped, key=lambda w: w.risk_score, reverse=True)[:5]
            return "Highest risk wells: " + "; ".join(f"{w.well_id} ({w.basin}, risk {w.risk_score}, {w.recommendation_category})" for w in top)
        if "operator" in q and ("highest leakage" in q or "exposure" in q):
            by_operator: dict[str, float] = {}
            for well in scoped:
                by_operator[well.operator_name] = by_operator.get(well.operator_name, 0) + well.revenue_leakage_daily
            ranked = sorted(by_operator.items(), key=lambda item: item[1], reverse=True)[:3]
            return "Operator leakage exposure: " + "; ".join(f"{name}: ${value:,.0f}/day" for name, value in ranked)
        if "forecast" in q or "next quarter" in q:
            leakage = sum(w.revenue_leakage_daily for w in scoped)
            return f"Next-quarter portfolio exposure is approximately ${leakage * 90:,.0f} if current shortfalls persist. Prioritize wells with high confidence and high daily leakage first."
        if "intervention" in q or "worked" in q:
            ranked = sorted(recommendations, key=lambda r: r.estimated_roi, reverse=True)[:5]
            return "Best intervention ROI candidates: " + "; ".join(f"{r.well_id} {r.category} ROI {r.estimated_roi}x" for r in ranked)
        if basin_match:
            flagged = [w for w in scoped if w.flagged]
            return f"{basin_match.group(1).upper()} has {len(flagged)} flagged wells with ${sum(w.revenue_leakage_daily for w in scoped):,.0f}/day modeled leakage. Top context: {context[0] if context else 'No matching well context.'}"
        return "Based on retrieved operating context: " + (context[0] if context else "No close match found. Try asking about risk, leakage, basin, forecast, or interventions.")


copilot_service = CopilotService()
