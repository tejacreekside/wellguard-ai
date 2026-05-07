from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from app.ml.decline import DeclineCurveModel
from app.ml.forecasting import ForecastingEngine
from app.models.schemas import ForecastPoint, PortfolioSummary, WellAnalysis, WellSummary


class AnalysisService:
    def __init__(self) -> None:
        self.curve = DeclineCurveModel()
        self.forecaster = ForecastingEngine()

    def analyze_portfolio(self, df: pd.DataFrame, oil_price: float = 70.0, threshold: float = 0.15) -> list[WellSummary]:
        return [self.analyze_well(well_df, oil_price, threshold) for _, well_df in df.groupby("well_id")]

    def analyze_well(self, well_df: pd.DataFrame, oil_price: float = 70.0, threshold: float = 0.15) -> WellSummary:
        ordered = well_df.sort_values("production_date").reset_index(drop=True)
        model = self.curve.fit(ordered)
        expected = self.curve.expected(len(ordered), model)
        latest = ordered.iloc[-1]
        latest_actual = float(latest["oil_bbl"])
        latest_expected = float(expected[-1]) if len(expected) else latest_actual
        variance_pct = ((latest_expected - latest_actual) / latest_expected) if latest_expected > 0 else 0.0
        flagged = variance_pct >= threshold or self._is_inactive_problem(ordered)
        severity = self._severity_score(ordered, expected, variance_pct, model.r2)
        leakage = max(latest_expected - latest_actual, 0.0) / 30.4375 * oil_price
        confidence = self.forecaster.confidence_score(ordered, model)
        category = self.recommendation_category(ordered, expected, flagged)
        risk = round(min(100, severity * 0.72 + max(0, variance_pct) * 100 * 0.28), 1)

        return WellSummary(
            well_id=str(latest["well_id"]),
            operator_name=str(latest["operator_name"]),
            basin=str(latest["basin"]),
            formation=str(latest["formation"]),
            status=str(latest["status"]),
            latest_oil_bbl=round(latest_actual, 2),
            expected_oil_bbl=round(latest_expected, 2),
            variance_pct=round(float(variance_pct), 4),
            severity_score=round(severity, 1),
            risk_score=risk,
            revenue_leakage_daily=round(float(leakage), 2),
            recommendation_category=category,
            confidence_score=confidence,
            flagged=bool(flagged),
        )

    def well_analysis(self, well_df: pd.DataFrame, oil_price: float = 70.0, threshold: float = 0.15) -> WellAnalysis:
        ordered = well_df.sort_values("production_date").reset_index(drop=True)
        model = self.curve.fit(ordered)
        expected = self.curve.expected(len(ordered), model)
        forecast_values = self.curve.forecast(len(ordered), 12, model)
        confidence = self.forecaster.confidence_score(ordered, model)
        start = pd.to_datetime(ordered["production_date"].max()) + pd.DateOffset(months=1)
        forecast = []
        spread = 0.25 + (100 - confidence) / 220
        for i, value in enumerate(forecast_values):
            month = (start + pd.DateOffset(months=i)).date()
            forecast.append(
                ForecastPoint(
                    production_date=month,
                    expected_oil_bbl=round(float(value), 2),
                    forecast_oil_bbl=round(float(value), 2),
                    lower_oil_bbl=round(float(max(value * (1 - spread), 0)), 2),
                    upper_oil_bbl=round(float(value * (1 + spread)), 2),
                )
            )
        history = ordered.copy()
        history["expected_oil_bbl"] = np.round(expected, 2)
        summary = self.analyze_well(ordered, oil_price, threshold)
        diagnostics = {
            "arps_parameters": {"qi": model.qi, "Di": model.di, "b": model.b},
            "model_r2": model.r2,
            "fit_message": model.message,
            "confidence_score": confidence,
            "future_loss_3_month_bbl": round(self.forecaster.future_loss(summary.expected_oil_bbl, summary.latest_oil_bbl, forecast_values[:3]), 2),
            "future_loss_6_month_bbl": round(self.forecaster.future_loss(summary.expected_oil_bbl, summary.latest_oil_bbl, forecast_values[:6]), 2),
            "future_loss_12_month_bbl": round(self.forecaster.future_loss(summary.expected_oil_bbl, summary.latest_oil_bbl, forecast_values), 2),
        }
        return WellAnalysis(well=summary, history=self._records(history), forecast=forecast, diagnostics=diagnostics)

    def portfolio_summary(self, summaries: list[WellSummary]) -> PortfolioSummary:
        flagged = [s for s in summaries if s.flagged]
        leakage = sum(s.revenue_leakage_daily for s in summaries)
        average_risk = float(np.mean([s.risk_score for s in summaries])) if summaries else 0.0
        health = round(max(0, 100 - average_risk - min(leakage / 5000, 20)), 1)
        return PortfolioSummary(
            portfolio_health_score=health,
            well_count=len(summaries),
            active_well_count=sum(s.status.lower() == "active" for s in summaries),
            flagged_well_count=len(flagged),
            total_daily_revenue_leakage=round(leakage, 2),
            estimated_30_day_leakage=round(leakage * 30, 2),
            top_bleeding_wells=sorted(summaries, key=lambda x: x.revenue_leakage_daily, reverse=True)[:10],
            risk_distribution={
                "low": sum(s.risk_score < 35 for s in summaries),
                "medium": sum(35 <= s.risk_score < 65 for s in summaries),
                "high": sum(s.risk_score >= 65 for s in summaries),
            },
        )

    def recommendation_category(self, ordered: pd.DataFrame, expected: np.ndarray, flagged: bool) -> str:
        recent = ordered.tail(4)
        oil = ordered["oil_bbl"].astype(float)
        water = ordered["water_bbl"].astype(float)
        missing_or_noisy = oil.pct_change().replace([np.inf, -np.inf], np.nan).dropna().abs().median() > 0.35
        if len(oil) >= 4 and (oil.tail(4) <= 0).all():
            return "shut-in / inactive review"
        if missing_or_noisy:
            return "data quality review"
        if flagged and len(recent) and recent["water_bbl"].sum() > recent["oil_bbl"].sum() * 0.9:
            return "artificial lift review"
        if flagged and len(oil) >= 8 and oil.iloc[-1] < oil.iloc[-5] * 0.72:
            return "workover candidate"
        if flagged:
            return "chemical treatment review"
        return "normal decline / no action"

    def _severity_score(self, ordered: pd.DataFrame, expected: np.ndarray, variance_pct: float, r2: float) -> float:
        recent_gap = max(variance_pct, 0) * 100
        zero_penalty = 25 if (ordered["oil_bbl"].tail(3) <= 0).all() else 0
        fit_bonus = max(r2, 0) * 10
        return float(max(0, min(100, recent_gap * 1.5 + zero_penalty + fit_bonus)))

    def _is_inactive_problem(self, ordered: pd.DataFrame) -> bool:
        return str(ordered.iloc[-1]["status"]).lower() == "inactive" and float(ordered.iloc[-1]["oil_bbl"]) <= 0

    def _records(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        output = df.copy()
        output["production_date"] = pd.to_datetime(output["production_date"]).dt.date.astype(str)
        return output.to_dict(orient="records")


analysis_service = AnalysisService()
