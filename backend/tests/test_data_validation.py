import pandas as pd
import pytest

from app.services.data_service import ProductionDataService


def test_missing_required_columns_returns_clear_error():
    service = ProductionDataService()
    with pytest.raises(ValueError, match="missing required columns"):
        service.clean_dataframe(pd.DataFrame({"well_id": ["A"], "oil_bbl": [10]}))


def test_cleaner_clips_negative_and_aggregates_duplicates():
    service = ProductionDataService()
    df = pd.DataFrame(
        [
            {
                "well_id": "A",
                "operator_name": "",
                "basin": "SCOOP",
                "formation": "Woodford",
                "production_date": "2025-01-01",
                "oil_bbl": -10,
                "gas_mcf": 20,
                "water_bbl": 5,
                "status": "active",
            },
            {
                "well_id": "A",
                "operator_name": "Kirkpatrick Oil",
                "basin": "SCOOP",
                "formation": "Woodford",
                "production_date": "2025-01-01",
                "oil_bbl": 100,
                "gas_mcf": 30,
                "water_bbl": 6,
                "status": "active",
            },
        ]
    )
    result = service.clean_dataframe(df)
    assert len(result.dataframe) == 1
    assert result.dataframe.iloc[0]["oil_bbl"] == 100
    assert any("negative" in warning for warning in result.warnings)
