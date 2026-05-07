from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


OPERATORS = [
    "Kirkpatrick Oil",
    "Crawley Petroleum",
    "Comanche Resources",
    "Mewbourne Oil",
    "Casillas Petroleum",
]
BASINS = ["SCOOP", "STACK", "Anadarko"]
FORMATIONS = ["Woodford", "Springer", "Meramec", "Osage"]


def arps(qi: float, di: float, b: float, t: np.ndarray) -> np.ndarray:
    return qi / np.power(1 + b * di * t, 1 / b)


def generate_sample_production_data(wells: int = 30, months: int = 36, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2023-01-01")
    rows: list[dict[str, object]] = []
    anomaly_count = min(wells, max(1, int(wells * 0.27)))
    anomalous = set(rng.choice(np.arange(wells), size=anomaly_count, replace=False))

    for idx in range(wells):
        well_id = f"OK-{1000 + idx}"
        operator = OPERATORS[idx % len(OPERATORS)]
        basin = BASINS[idx % len(BASINS)]
        formation = FORMATIONS[idx % len(FORMATIONS)]
        qi = float(rng.uniform(4200, 12500))
        di = float(rng.uniform(0.035, 0.09))
        b = float(rng.uniform(0.55, 1.25))
        t = np.arange(months)
        base = arps(qi, di, b, t)
        oil = np.maximum(base * rng.normal(1.0, 0.055, months), 0)
        anomaly_type = "normal"

        if idx in anomalous:
            anomaly_type = rng.choice(["sudden_drop", "water_rise", "zero_flat", "noisy_data", "negative_mess"])
            if anomaly_type == "sudden_drop":
                oil[22:] *= rng.uniform(0.45, 0.7)
            elif anomaly_type == "water_rise":
                oil[24:] *= rng.uniform(0.6, 0.78)
            elif anomaly_type == "zero_flat":
                oil[28:] = 0
            elif anomaly_type == "noisy_data":
                oil *= rng.normal(1.0, 0.22, months)
                oil[rng.choice(t, 3, replace=False)] = np.nan
            elif anomaly_type == "negative_mess":
                oil[rng.choice(t, 2, replace=False)] = -rng.uniform(40, 200)

        gas = np.maximum(oil * rng.uniform(1.8, 3.9) * rng.normal(1.0, 0.08, months), 0)
        water_factor = rng.uniform(0.12, 0.7)
        water = np.maximum(oil * water_factor * (1 + t / months) * rng.normal(1.0, 0.12, months), 0)
        if anomaly_type == "water_rise":
            water[24:] *= rng.uniform(2.0, 3.8)

        for month in range(months):
            if anomaly_type == "noisy_data" and month in {11, 12}:
                continue
            status = "inactive" if anomaly_type == "zero_flat" and month >= 28 else "active"
            rows.append(
                {
                    "well_id": well_id,
                    "operator_name": operator,
                    "basin": basin,
                    "formation": formation,
                    "production_date": (start + pd.DateOffset(months=month)).date().isoformat(),
                    "oil_bbl": round(float(oil[month]) if not np.isnan(oil[month]) else np.nan, 2),
                    "gas_mcf": round(float(gas[month]), 2),
                    "water_bbl": round(float(water[month]), 2),
                    "status": status,
                }
            )

        if idx % 9 == 0:
            rows.append(rows[-1].copy())

    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def write_sample_csv(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    generate_sample_production_data().to_csv(output, index=False)
    return output


if __name__ == "__main__":
    write_sample_csv(Path(__file__).resolve().parents[3] / "data" / "sample_production_data.csv")
