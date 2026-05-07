from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from app.models.schemas import INTERNAL_COLUMNS, DataQualityReport


COLUMN_ALIASES = {
    "well_id": [
        "well_id",
        "well name",
        "well_name",
        "lease_name",
        "lease",
        "well",
        "completion_name",
    ],
    "api_number": ["api_number", "api", "api no", "api_no", "api10", "api 10", "api_10", "api well number"],
    "operator_name": ["operator_name", "operator", "operator name", "current operator", "company"],
    "basin": ["basin", "play", "region"],
    "formation": ["formation", "producing formation", "reservoir", "common source of supply", "zone"],
    "county": ["county", "county_name"],
    "state": ["state", "st"],
    "production_date": ["production_date", "prod_date", "production month", "month", "prod month", "date", "period"],
    "oil_bbl": ["oil_bbl", "oil", "oil volume", "oil_bbls", "oil barrels", "oil production", "oil_prod"],
    "gas_mcf": ["gas_mcf", "gas", "gas volume", "gas_mcf_prod", "gas production", "gas_prod"],
    "water_bbl": ["water_bbl", "water", "water volume", "water_bbls", "water production", "water_prod"],
    "status": ["status", "well_status", "well status", "active status"],
    "latitude": ["latitude", "lat", "surface latitude"],
    "longitude": ["longitude", "lon", "long", "surface longitude"],
}

OPERATOR_SUFFIXES = [" LLC", " INC", " INC.", " CO", " COMPANY", " CORPORATION", " CORP", " LP", " LTD"]


@dataclass
class ETLResult:
    dataframe: pd.DataFrame
    quality: DataQualityReport
    warnings: list[str] = field(default_factory=list)


class OCCETLService:
    """Normalizes OCC/OTC-style well production exports into WellGuard's schema."""

    def read_file(self, path: str | Path) -> pd.DataFrame:
        source = Path(path)
        if source.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(source)
        return pd.read_csv(source)

    def normalize_file(self, path: str | Path) -> ETLResult:
        return self.normalize_dataframe(self.read_file(path))

    def normalize_dataframe(self, raw: pd.DataFrame) -> ETLResult:
        warnings: list[str] = []
        rows_received = len(raw)
        if raw.empty:
            raise ValueError("OCC/OTC production file is empty.")

        df = raw.copy()
        df.columns = [self._clean_header(c) for c in df.columns]
        mapping = self._build_mapping(df.columns)
        normalized = pd.DataFrame()
        for internal in INTERNAL_COLUMNS:
            source = mapping.get(internal)
            normalized[internal] = df[source] if source else None

        if not mapping.get("production_date"):
            raise ValueError("Unable to locate a production date column in OCC/OTC file.")
        if not mapping.get("oil_bbl") and not mapping.get("gas_mcf") and not mapping.get("water_bbl"):
            raise ValueError("Unable to locate production volume columns in OCC/OTC file.")

        missing_identity = normalized["well_id"].isna() & normalized["api_number"].isna()
        if missing_identity.any():
            warnings.append(f"Dropped {int(missing_identity.sum())} rows without well name/API identifier.")
            normalized = normalized[~missing_identity]

        normalized["api_number"] = normalized["api_number"].fillna("").astype(str).str.replace(r"\D", "", regex=True)
        normalized["well_id"] = normalized["well_id"].fillna("").astype(str).str.strip()
        normalized.loc[normalized["well_id"] == "", "well_id"] = "API-" + normalized["api_number"]
        normalized["operator_name"] = normalized["operator_name"].fillna("Unknown").map(self.normalize_operator_name)
        normalized["basin"] = normalized["basin"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
        normalized["formation"] = normalized["formation"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
        normalized["county"] = normalized["county"].fillna("Unknown").astype(str).str.title().replace("", "Unknown")
        normalized["state"] = normalized["state"].fillna("OK").astype(str).str.upper().replace("", "OK")
        normalized["status"] = normalized["status"].fillna("active").astype(str).str.lower().replace("", "active")

        dates = pd.to_datetime(normalized["production_date"], errors="coerce")
        malformed_dates = int(dates.isna().sum())
        if malformed_dates:
            warnings.append(f"Dropped {malformed_dates} rows with malformed production dates.")
        normalized = normalized.loc[~dates.isna()].copy()
        normalized["production_date"] = dates.loc[~dates.isna()].dt.to_period("M").dt.to_timestamp()

        clipped_negative_values = 0
        corrupted_numeric = 0
        for col in ["oil_bbl", "gas_mcf", "water_bbl", "latitude", "longitude"]:
            values = pd.to_numeric(normalized[col], errors="coerce")
            corrupted_numeric += int(values.isna().sum() - normalized[col].isna().sum())
            normalized[col] = values.fillna(0.0 if col.endswith(("bbl", "mcf")) else pd.NA)
            if col in {"oil_bbl", "gas_mcf", "water_bbl"}:
                negatives = normalized[col] < 0
                clipped_negative_values += int(negatives.sum())
                normalized.loc[negatives, col] = 0.0

        duplicates = int(normalized.duplicated(subset=["well_id", "production_date"]).sum())
        if duplicates:
            warnings.append(f"Aggregated {duplicates} duplicate well/month production records.")
        normalized = (
            normalized.groupby(["well_id", "production_date"], as_index=False, dropna=False)
            .agg(
                api_number=("api_number", "first"),
                operator_name=("operator_name", "first"),
                basin=("basin", "first"),
                formation=("formation", "first"),
                county=("county", "first"),
                state=("state", "first"),
                oil_bbl=("oil_bbl", "sum"),
                gas_mcf=("gas_mcf", "sum"),
                water_bbl=("water_bbl", "sum"),
                status=("status", "last"),
                latitude=("latitude", "first"),
                longitude=("longitude", "first"),
            )
            .sort_values(["well_id", "production_date"])
        )

        inactive_mask = (normalized["oil_bbl"] <= 0) & (normalized["gas_mcf"] <= 0) & (normalized["water_bbl"] <= 0)
        normalized.loc[inactive_mask, "status"] = normalized.loc[inactive_mask, "status"].replace({"active": "inactive"})

        missing_required_values = int(normalized[["operator_name", "production_date"]].isna().sum().sum())
        if corrupted_numeric:
            warnings.append(f"Converted {corrupted_numeric} corrupted numeric values to null/zero.")
        if clipped_negative_values:
            warnings.append(f"Clipped {clipped_negative_values} negative production values to zero.")

        quality_score = self._quality_score(
            rows_received=rows_received,
            rows_loaded=len(normalized),
            malformed_dates=malformed_dates,
            duplicates=duplicates,
            clipped_negative_values=clipped_negative_values,
            missing_required_values=missing_required_values,
            corrupted_numeric=corrupted_numeric,
        )
        quality = DataQualityReport(
            score=quality_score,
            rows_received=rows_received,
            rows_loaded=len(normalized),
            duplicate_rows=duplicates,
            malformed_dates=malformed_dates,
            clipped_negative_values=clipped_negative_values,
            missing_required_values=missing_required_values,
            warnings=warnings,
        )
        return ETLResult(normalized[INTERNAL_COLUMNS], quality, warnings)

    def normalize_operator_name(self, value: Any) -> str:
        text = str(value or "Unknown").strip().upper()
        for suffix in OPERATOR_SUFFIXES:
            if text.endswith(suffix):
                text = text[: -len(suffix)]
        return " ".join(text.title().split()) or "Unknown"

    def _build_mapping(self, columns: pd.Index) -> dict[str, str]:
        available = {self._clean_header(c): c for c in columns}
        mapping: dict[str, str] = {}
        for internal, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                clean = self._clean_header(alias)
                if clean in available:
                    mapping[internal] = available[clean]
                    break
        return mapping

    def _clean_header(self, value: Any) -> str:
        return str(value).strip().lower().replace("_", " ").replace("-", " ")

    def _quality_score(
        self,
        rows_received: int,
        rows_loaded: int,
        malformed_dates: int,
        duplicates: int,
        clipped_negative_values: int,
        missing_required_values: int,
        corrupted_numeric: int,
    ) -> float:
        if rows_received <= 0:
            return 0.0
        penalties = (
            malformed_dates * 2.0
            + duplicates * 0.35
            + clipped_negative_values * 1.5
            + missing_required_values * 2.5
            + corrupted_numeric * 0.75
            + max(rows_received - rows_loaded, 0) * 1.0
        )
        return round(max(5.0, min(100.0, 100.0 - penalties / rows_received * 100)), 1)


occ_etl_service = OCCETLService()
