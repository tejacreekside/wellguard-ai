from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from app.core.config import get_settings
from app.data.sample_generator import generate_sample_production_data, write_sample_csv
from app.models.schemas import REQUIRED_COLUMNS


@dataclass
class DataLoadResult:
    dataframe: pd.DataFrame
    warnings: list[str] = field(default_factory=list)


class ProductionDataService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._dataframe: pd.DataFrame | None = None
        self._warnings: list[str] = []

    @property
    def dataframe(self) -> pd.DataFrame:
        if self._dataframe is None or self._dataframe.empty:
            sample_path = self.settings.data_dir / "sample_production_data.csv"
            if not sample_path.exists():
                write_sample_csv(sample_path)
            result = self.load_csv(sample_path)
            self._dataframe = result.dataframe
            self._warnings = result.warnings
        return self._dataframe.copy()

    @property
    def warnings(self) -> list[str]:
        return list(self._warnings)

    def load_synthetic(self) -> DataLoadResult:
        result = self.clean_dataframe(generate_sample_production_data())
        self._dataframe = result.dataframe
        self._warnings = result.warnings
        return result

    def load_csv(self, path: str | Path) -> DataLoadResult:
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            raise ValueError("Uploaded file is empty. Provide a CSV with production records.")
        except Exception as exc:
            raise ValueError(f"Could not read CSV: {exc}") from exc
        result = self.clean_dataframe(df)
        self._dataframe = result.dataframe
        self._warnings = result.warnings
        return result

    def clean_dataframe(self, df: pd.DataFrame) -> DataLoadResult:
        warnings: list[str] = []
        if df.empty:
            raise ValueError("Production dataset is empty.")

        df = df.copy()
        df.columns = [str(c).strip().lower() for c in df.columns]
        missing = sorted(REQUIRED_COLUMNS - set(df.columns))
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

        df = df[list(REQUIRED_COLUMNS)].copy()
        for col in ["operator_name", "basin", "formation", "status"]:
            blank_count = df[col].isna().sum() + (df[col].astype(str).str.strip() == "").sum()
            if blank_count:
                warnings.append(f"Filled {int(blank_count)} missing {col} values.")
            df[col] = df[col].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")

        df["well_id"] = df["well_id"].astype(str).str.strip()
        df = df[df["well_id"] != ""]
        df["production_date"] = pd.to_datetime(df["production_date"], errors="coerce")
        bad_dates = int(df["production_date"].isna().sum())
        if bad_dates:
            warnings.append(f"Dropped {bad_dates} rows with malformed dates.")
            df = df.dropna(subset=["production_date"])

        for col in ["oil_bbl", "gas_mcf", "water_bbl"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            missing_values = int(df[col].isna().sum())
            if missing_values:
                warnings.append(f"Converted {missing_values} missing/non-numeric {col} values to 0.")
            df[col] = df[col].fillna(0.0)
            negatives = int((df[col] < 0).sum())
            if negatives:
                warnings.append(f"Clipped {negatives} negative {col} values to 0.")
                df.loc[df[col] < 0, col] = 0.0

        duplicates = int(df.duplicated(subset=["well_id", "production_date"]).sum())
        if duplicates:
            warnings.append(f"Aggregated {duplicates} duplicate well/date rows.")
        df = (
            df.groupby(["well_id", "production_date"], as_index=False)
            .agg(
                operator_name=("operator_name", "first"),
                basin=("basin", "first"),
                formation=("formation", "first"),
                oil_bbl=("oil_bbl", "sum"),
                gas_mcf=("gas_mcf", "sum"),
                water_bbl=("water_bbl", "sum"),
                status=("status", "last"),
            )
            .sort_values(["well_id", "production_date"])
        )

        clipped = 0
        for well_id, well_df in df.groupby("well_id"):
            q99 = well_df["oil_bbl"].quantile(0.99)
            if q99 > 0:
                mask = (df["well_id"] == well_id) & (df["oil_bbl"] > q99 * 1.8)
                clipped += int(mask.sum())
                df.loc[mask, "oil_bbl"] = q99 * 1.8
        if clipped:
            warnings.append(f"Clipped {clipped} extreme oil outliers.")

        return DataLoadResult(df.reset_index(drop=True), warnings)


data_service = ProductionDataService()
