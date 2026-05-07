from __future__ import annotations

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import Base, engine
from app.core.logging import get_logger
from app.models.db import Operator, ProductionHistory, Well


logger = get_logger(__name__)


class PersistenceService:
    def init_db(self) -> None:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("database_schema_ready")
        except SQLAlchemyError as exc:
            logger.warning("database_schema_init_failed:%s", exc)

    def replace_production_dataset(self, db: Session, df: pd.DataFrame) -> None:
        db.execute(delete(ProductionHistory))
        db.execute(delete(Well))
        db.execute(delete(Operator))
        operators: dict[str, Operator] = {}
        for _, meta in df.groupby("well_id").tail(1).iterrows():
            op_name = str(meta.get("operator_name") or "Unknown")
            operator = operators.get(op_name)
            if operator is None:
                operator = Operator(name=op_name, normalized_name=op_name.upper())
                db.add(operator)
                db.flush()
                operators[op_name] = operator
            db.add(
                Well(
                    well_id=str(meta["well_id"]),
                    api_number=str(meta.get("api_number") or ""),
                    operator_id=operator.id,
                    basin=str(meta.get("basin") or "Unknown"),
                    formation=str(meta.get("formation") or "Unknown"),
                    county=str(meta.get("county") or "Unknown"),
                    state=str(meta.get("state") or "OK"),
                    status=str(meta.get("status") or "active"),
                    latitude=self._nullable_float(meta.get("latitude")),
                    longitude=self._nullable_float(meta.get("longitude")),
                    data_quality_score=100,
                )
            )
        db.flush()
        records = []
        for _, row in df.iterrows():
            records.append(
                ProductionHistory(
                    well_id=str(row["well_id"]),
                    production_date=pd.to_datetime(row["production_date"]).date(),
                    oil_bbl=float(row.get("oil_bbl") or 0),
                    gas_mcf=float(row.get("gas_mcf") or 0),
                    water_bbl=float(row.get("water_bbl") or 0),
                )
            )
        db.add_all(records)
        db.commit()
        logger.info("production_dataset_persisted rows=%s wells=%s", len(df), df["well_id"].nunique())

    def load_dataframe(self, db: Session) -> pd.DataFrame:
        stmt = (
            select(
                Well.well_id,
                Well.api_number,
                Operator.name.label("operator_name"),
                Well.basin,
                Well.formation,
                Well.county,
                Well.state,
                ProductionHistory.production_date,
                ProductionHistory.oil_bbl,
                ProductionHistory.gas_mcf,
                ProductionHistory.water_bbl,
                Well.status,
                Well.latitude,
                Well.longitude,
            )
            .join(Operator, Operator.id == Well.operator_id)
            .join(ProductionHistory, ProductionHistory.well_id == Well.well_id)
        )
        rows = db.execute(stmt).mappings().all()
        return pd.DataFrame(rows)

    def _nullable_float(self, value) -> float | None:
        try:
            if pd.isna(value):
                return None
            return float(value)
        except Exception:
            return None


persistence_service = PersistenceService()
