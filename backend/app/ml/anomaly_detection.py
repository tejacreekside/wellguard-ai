from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class DetectedAnomaly:
    anomaly_type: str
    severity: float
    production_date: pd.Timestamp
    explanation: str
    confidence_score: float


class AnomalyDetectionEngine:
    def detect(self, well_df: pd.DataFrame, expected: np.ndarray) -> list[DetectedAnomaly]:
        ordered = well_df.sort_values("production_date").reset_index(drop=True)
        oil = ordered["oil_bbl"].astype(float)
        water = ordered["water_bbl"].astype(float)
        dates = pd.to_datetime(ordered["production_date"])
        anomalies: list[DetectedAnomaly] = []
        if len(ordered) < 4:
            return anomalies

        latest_gap = (expected[-1] - oil.iloc[-1]) / expected[-1] if expected[-1] > 0 else 0
        pct = oil.pct_change().replace([np.inf, -np.inf], np.nan)
        trailing_decline = (oil.iloc[-4] - oil.iloc[-1]) / max(oil.iloc[-4], 1)
        water_cut_now = water.tail(3).sum() / max((oil.tail(3).sum() + water.tail(3).sum()), 1)
        water_cut_prior = water.iloc[-9:-6].sum() / max((oil.iloc[-9:-6].sum() + water.iloc[-9:-6].sum()), 1) if len(oil) >= 9 else 0

        if pct.iloc[-1] < -0.30:
            anomalies.append(self._make("sudden_drop", min(abs(pct.iloc[-1]) * 100, 100), dates.iloc[-1], "Latest month declined more than 30% from the prior producing month.", 86))
        if latest_gap > 0.20 and trailing_decline > 0.18:
            anomalies.append(self._make("accelerated_decline", min(latest_gap * 120, 100), dates.iloc[-1], "Actual production is materially below the selected decline curve and trailing decline is accelerating.", 82))
        if oil.tail(4).std() < max(oil.tail(12).std() * 0.25, 1) and oil.tail(4).mean() > 0 and latest_gap > 0.15:
            anomalies.append(self._make("abnormal_flattening", min(latest_gap * 100, 80), dates.iloc[-1], "Recent oil production flattened abnormally below modeled expectation.", 72))
        if (oil.tail(8) <= 0).sum() >= 3 and (oil.tail(8) > 0).sum() >= 2:
            anomalies.append(self._make("intermittent_production", 70, dates.iloc[-1], "Recent history alternates between zero and producing months.", 78))
        if (oil.tail(4) <= 0).all():
            anomalies.append(self._make("shut_in_behavior", 95, dates.iloc[-1], "Well has four consecutive zero-oil months.", 90))
        if water_cut_now - water_cut_prior > 0.18 and latest_gap > 0.12:
            anomalies.append(self._make("high_water_anomaly", min((water_cut_now - water_cut_prior) * 180, 100), dates.iloc[-1], "Water cut increased materially while oil production underperformed.", 84))
        if water.tail(3).sum() > oil.tail(3).sum() * 1.2 and latest_gap > 0.12:
            anomalies.append(self._make("potential_artificial_lift_issue", min(latest_gap * 110, 95), dates.iloc[-1], "High water handling load coincides with oil shortfall.", 76))
        return anomalies

    def _make(self, anomaly_type: str, severity: float, date: pd.Timestamp, explanation: str, confidence: float) -> DetectedAnomaly:
        return DetectedAnomaly(anomaly_type, round(float(severity), 1), date, explanation, confidence)
