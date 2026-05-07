from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score


def arps_decline(t: np.ndarray, qi: float, di: float, b: float) -> np.ndarray:
    return qi / np.power(1 + b * di * np.maximum(t, 0), 1 / b)


@dataclass
class DeclineModelResult:
    qi: float
    di: float
    b: float
    r2: float
    fitted: bool
    message: str


class DeclineCurveModel:
    def fit(self, well_df: pd.DataFrame) -> DeclineModelResult:
        ordered = well_df.sort_values("production_date").reset_index(drop=True)
        y = ordered["oil_bbl"].astype(float).to_numpy()
        t = np.arange(len(y), dtype=float)
        positive = y > 0

        if len(y) < 6:
            return DeclineModelResult(float(max(y.max(initial=0), 1)), 0.05, 0.9, 0.0, False, "Too few data points for reliable curve fit.")
        if positive.sum() < 4:
            return DeclineModelResult(float(max(y.max(initial=0), 1)), 0.05, 0.9, 0.0, False, "Insufficient positive production history.")

        try:
            popt, _ = curve_fit(
                arps_decline,
                t[positive],
                y[positive],
                p0=[max(y[positive][0], y[positive].max()), 0.06, 0.8],
                bounds=([1, 0.001, 0.05], [50000, 0.35, 2.0]),
                maxfev=20000,
            )
            expected = arps_decline(t[positive], *popt)
            r2 = float(r2_score(y[positive], expected)) if len(expected) > 1 else 0.0
            return DeclineModelResult(float(popt[0]), float(popt[1]), float(popt[2]), max(min(r2, 1), -1), True, "Curve fit completed.")
        except Exception as exc:
            qi = float(max(y[positive].max(initial=0), 1))
            return DeclineModelResult(qi, 0.05, 0.9, 0.0, False, f"Curve fit failed; fallback decline used: {exc}")

    def expected(self, length: int, model: DeclineModelResult) -> np.ndarray:
        return arps_decline(np.arange(length, dtype=float), model.qi, model.di, model.b)

    def forecast(self, history_length: int, horizon_months: int, model: DeclineModelResult) -> np.ndarray:
        t = np.arange(history_length, history_length + horizon_months, dtype=float)
        return arps_decline(t, model.qi, model.di, model.b)
