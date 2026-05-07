from __future__ import annotations

from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.agents.workflow import workflow
from app.core.config import get_settings
from app.models.schemas import AnalysisRequest, UploadResponse
from app.services.analysis_service import analysis_service
from app.services.data_service import data_service


router = APIRouter()


def _summaries(oil_price: Optional[float] = None, threshold: Optional[float] = None):
    settings = get_settings()
    return analysis_service.analyze_portfolio(
        data_service.dataframe,
        oil_price or settings.default_oil_price,
        threshold or settings.default_decline_threshold,
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "WellGuard AI"}


@router.post("/upload-production-data", response_model=UploadResponse)
async def upload_production_data(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp:
            tmp.write(content)
            tmp.flush()
            result = data_service.load_csv(tmp.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UploadResponse(
        rows_ingested=len(result.dataframe),
        wells_loaded=int(result.dataframe["well_id"].nunique()),
        warnings=result.warnings,
    )


@router.post("/run-analysis")
def run_analysis(request: AnalysisRequest) -> dict[str, object]:
    summaries = _summaries(request.oil_price, request.threshold)
    portfolio = analysis_service.portfolio_summary(summaries)
    return {"portfolio": portfolio, "agent_telemetry": workflow.telemetry(summaries)}


@router.get("/portfolio/summary")
def portfolio_summary(
    oil_price: float = Query(default=70.0, gt=0, le=300),
    threshold: float = Query(default=0.15, gt=0, lt=0.9),
):
    return analysis_service.portfolio_summary(_summaries(oil_price, threshold))


@router.get("/wells")
def wells(
    operator: Optional[str] = None,
    basin: Optional[str] = None,
    formation: Optional[str] = None,
    oil_price: float = Query(default=70.0, gt=0, le=300),
    threshold: float = Query(default=0.15, gt=0, lt=0.9),
):
    summaries = _summaries(oil_price, threshold)
    if operator:
        summaries = [w for w in summaries if w.operator_name == operator]
    if basin:
        summaries = [w for w in summaries if w.basin == basin]
    if formation:
        summaries = [w for w in summaries if w.formation == formation]
    return sorted(summaries, key=lambda x: x.risk_score, reverse=True)


@router.get("/wells/{well_id}/analysis")
def well_analysis(well_id: str, oil_price: float = Query(default=70.0, gt=0, le=300), threshold: float = Query(default=0.15, gt=0, lt=0.9)):
    df = data_service.dataframe
    well_df = df[df["well_id"] == well_id]
    if well_df.empty:
        raise HTTPException(status_code=404, detail=f"Well {well_id} was not found.")
    return analysis_service.well_analysis(well_df, oil_price, threshold)


@router.get("/wells/{well_id}/forecast")
def well_forecast(well_id: str):
    return well_analysis(well_id).forecast


@router.get("/recommendations")
def recommendations(oil_price: float = Query(default=70.0, gt=0, le=300), threshold: float = Query(default=0.15, gt=0, lt=0.9)):
    return workflow.recommendations(_summaries(oil_price, threshold))


@router.get("/executive-summary")
def executive_summary(oil_price: float = Query(default=70.0, gt=0, le=300), threshold: float = Query(default=0.15, gt=0, lt=0.9)):
    summaries = _summaries(oil_price, threshold)
    portfolio = analysis_service.portfolio_summary(summaries)
    return workflow.executive_summary(portfolio, summaries)


@router.get("/reports/intervention-report.csv")
def intervention_report(oil_price: float = Query(default=70.0, gt=0, le=300), threshold: float = Query(default=0.15, gt=0, lt=0.9)):
    recs = workflow.recommendations(_summaries(oil_price, threshold))
    rows = "well_id,priority,category,rationale,suggested_next_step\n"
    for rec in recs:
        safe = [rec.well_id, rec.priority, rec.category, rec.rationale, rec.suggested_next_step]
        rows += ",".join('"' + item.replace('"', '""') + '"' for item in safe) + "\n"
    return StreamingResponse(iter([rows]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=wellguard_intervention_report.csv"})
