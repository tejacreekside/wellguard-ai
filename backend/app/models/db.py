from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Operator(Base):
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    wells: Mapped[list["Well"]] = relationship(back_populates="operator")


class Well(Base):
    __tablename__ = "wells"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    well_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    api_number: Mapped[str] = mapped_column(String(40), index=True, default="")
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"))
    basin: Mapped[str] = mapped_column(String(120), index=True, default="Unknown")
    formation: Mapped[str] = mapped_column(String(120), index=True, default="Unknown")
    county: Mapped[str] = mapped_column(String(120), index=True, default="Unknown")
    state: Mapped[str] = mapped_column(String(8), default="OK")
    status: Mapped[str] = mapped_column(String(40), default="active")
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_quality_score: Mapped[float] = mapped_column(Float, default=100)
    operator: Mapped[Operator] = relationship(back_populates="wells")
    production: Mapped[list["ProductionHistory"]] = relationship(back_populates="well")


class ProductionHistory(Base):
    __tablename__ = "production_history"
    __table_args__ = (
        UniqueConstraint("well_id", "production_date", name="uq_well_production_month"),
        Index("ix_production_well_date", "well_id", "production_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.well_id"), index=True)
    production_date: Mapped[date] = mapped_column(Date, index=True)
    oil_bbl: Mapped[float] = mapped_column(Float, default=0)
    gas_mcf: Mapped[float] = mapped_column(Float, default=0)
    water_bbl: Mapped[float] = mapped_column(Float, default=0)
    well: Mapped[Well] = relationship(back_populates="production")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    well_id: Mapped[str] = mapped_column(String(120), index=True)
    anomaly_type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[float] = mapped_column(Float)
    production_date: Mapped[date] = mapped_column(Date)
    explanation: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float)


class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    well_id: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    priority: Mapped[str] = mapped_column(String(40))
    rationale: Mapped[str] = mapped_column(Text)
    expected_recovery_bbl_month: Mapped[float] = mapped_column(Float, default=0)
    estimated_roi: Mapped[float] = mapped_column(Float, default=0)
    payback_days: Mapped[float] = mapped_column(Float, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, default=70)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ForecastRecord(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    well_id: Mapped[str] = mapped_column(String(120), index=True)
    production_date: Mapped[date] = mapped_column(Date, index=True)
    model_name: Mapped[str] = mapped_column(String(80))
    forecast_oil_bbl: Mapped[float] = mapped_column(Float)
    lower_oil_bbl: Mapped[float] = mapped_column(Float)
    upper_oil_bbl: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float)
