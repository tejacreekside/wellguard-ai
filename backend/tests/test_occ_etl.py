import pandas as pd

from app.services.occ_etl_service import OCCETLService


def test_occ_normalizer_maps_alias_columns_and_scores_quality():
    raw = pd.DataFrame(
        [
            {
                "API": "3501723456",
                "Well Name": "Jones 1-12H",
                "Operator": "ACME ENERGY LLC",
                "County": "kingfisher",
                "Production Month": "2025-01",
                "Oil": "1200",
                "Gas": "3400",
                "Water": "500",
            },
            {
                "API": "3501723456",
                "Well Name": "Jones 1-12H",
                "Operator": "ACME ENERGY LLC",
                "County": "kingfisher",
                "Production Month": "2025-01",
                "Oil": "-5",
                "Gas": "bad",
                "Water": "10",
            },
        ]
    )
    result = OCCETLService().normalize_dataframe(raw)
    assert len(result.dataframe) == 1
    assert result.dataframe.iloc[0]["operator_name"] == "Acme Energy"
    assert result.dataframe.iloc[0]["oil_bbl"] == 1200
    assert result.quality.duplicate_rows == 1
    assert result.quality.score < 100


def test_occ_normalizer_rejects_missing_date_column():
    raw = pd.DataFrame([{"API": "3501", "Oil": 100}])
    try:
        OCCETLService().normalize_dataframe(raw)
    except ValueError as exc:
        assert "production date" in str(exc)
    else:
        raise AssertionError("Expected invalid OCC file to fail clearly.")
