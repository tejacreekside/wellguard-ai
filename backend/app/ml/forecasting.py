from __future__ import annotations

import numpy as np
import pandas as pd

from app.ml.decline import DeclineCurveModel, DeclineModelResult


class ForecastingEngine:
    def __init__(self) -> None:
        self.decline_model = DeclineCurveModel()

    def confidence_score(self, well_df: pd.DataFrame, model: DeclineModelResult) -> float:
        ordered = well_df.sort_values("production_date")
        missing_months = max(self._missing_months(ordered), 0)
        zero_ratio = float((ordered["oil_bbl"] <= 0).mean()) if len(ordered) else 1.0
        variation = float(ordered["oil_bbl"].pct_change().replace([np.inf, -np.inf], np.nan).dropna().abs().median() or 0)
        data_depth = min(len(ordered) / 24, 1.0)
        fit = max(model.r2, 0.0)
        quality = 1 - min(missing_months / 6, 0.35) - min(zero_ratio, 0.35) - min(variation, 0.25)
        score = 100 * (0.35 * data_depth + 0.4 * fit + 0.25 * max(quality, 0))
        return round(float(max(5, min(score, 98))), 1)

    def future_loss(self, latest_expected: float, latest_actual: float, forecast: np.ndarray) -> float:
        gap_ratio = max((latest_expected - latest_actual) / latest_expected, 0) if latest_expected > 0 else 0
        return float(np.sum(forecast * gap_ratio))

    def _missing_months(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        dates = pd.to_datetime(df["production_date"])
        expected = pd.period_range(dates.min(), dates.max(), freq="M")
        actual = dates.dt.to_period("M").unique()
        return len(set(expected) - set(actual))
