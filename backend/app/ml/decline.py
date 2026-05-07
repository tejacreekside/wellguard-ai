from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score


def arps_decline(t: np.ndarray, qi: float, di: float, b: float) -> np.ndarray:
    return qi / np.power(1 + b * di * np.maximum(t, 0), 1 / b)


def exponential_decline(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    return qi * np.exp(-di * np.maximum(t, 0))


def harmonic_decline(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    return qi / (1 + di * np.maximum(t, 0))


@dataclass
class DeclineModelResult:
    model_name: str
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
            return DeclineModelResult("fallback", float(max(y.max(initial=0), 1)), 0.05, 0.9, 0.0, False, "Too few data points for reliable curve fit.")
        if positive.sum() < 4:
            return DeclineModelResult("fallback", float(max(y.max(initial=0), 1)), 0.05, 0.9, 0.0, False, "Insufficient positive production history.")

        candidates: list[DeclineModelResult] = []
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
            candidates.append(DeclineModelResult("hyperbolic", float(popt[0]), float(popt[1]), float(popt[2]), max(min(r2, 1), -1), True, "Hyperbolic curve fit completed."))
        except Exception:
            pass

        for name, fn in [("exponential", exponential_decline), ("harmonic", harmonic_decline)]:
            try:
                popt, _ = curve_fit(
                    fn,
                    t[positive],
                    y[positive],
                    p0=[max(y[positive][0], y[positive].max()), 0.05],
                    bounds=([1, 0.001], [50000, 0.35]),
                    maxfev=20000,
                )
                expected = fn(t[positive], *popt)
                r2 = float(r2_score(y[positive], expected)) if len(expected) > 1 else 0.0
                candidates.append(DeclineModelResult(name, float(popt[0]), float(popt[1]), 1.0 if name == "harmonic" else 0.0, max(min(r2, 1), -1), True, f"{name.title()} curve fit completed."))
            except Exception:
                continue

        if candidates:
            return sorted(candidates, key=lambda result: result.r2, reverse=True)[0]
        qi = float(max(y[positive].max(initial=0), 1))
        return DeclineModelResult("fallback", qi, 0.05, 0.9, 0.0, False, "All decline fits failed; fallback decline used.")

    def expected(self, length: int, model: DeclineModelResult) -> np.ndarray:
        t = np.arange(length, dtype=float)
        return self._predict(t, model)

    def forecast(self, history_length: int, horizon_months: int, model: DeclineModelResult) -> np.ndarray:
        t = np.arange(history_length, history_length + horizon_months, dtype=float)
        return self._predict(t, model)

    def _predict(self, t: np.ndarray, model: DeclineModelResult) -> np.ndarray:
        if model.model_name == "exponential":
            return exponential_decline(t, model.qi, model.di)
        if model.model_name == "harmonic":
            return harmonic_decline(t, model.qi, model.di)
        return arps_decline(t, model.qi, model.di, model.b)
