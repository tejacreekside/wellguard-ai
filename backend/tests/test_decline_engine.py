import pandas as pd

from app.data.sample_generator import generate_sample_production_data
from app.ml.decline import DeclineCurveModel
from app.services.analysis_service import AnalysisService


def test_decline_curve_fits_sample_well():
    df = generate_sample_production_data(wells=1, months=24)
    model = DeclineCurveModel().fit(df)
    assert model.qi > 0
    assert 0.001 <= model.di <= 0.35
    assert model.b > 0


def test_anomaly_detection_flags_sudden_drop():
    rows = []
    for month in range(18):
        oil = 1000 - month * 20
        if month >= 15:
            oil *= 0.45
        rows.append(
            {
                "well_id": "A",
                "operator_name": "Kirkpatrick Oil",
                "basin": "STACK",
                "formation": "Meramec",
                "production_date": pd.Timestamp("2024-01-01") + pd.DateOffset(months=month),
                "oil_bbl": oil,
                "gas_mcf": oil * 2,
                "water_bbl": oil * 0.2,
                "status": "active",
            }
        )
    summary = AnalysisService().analyze_well(pd.DataFrame(rows), oil_price=70, threshold=0.15)
    assert summary.flagged
    assert summary.revenue_leakage_daily > 0
