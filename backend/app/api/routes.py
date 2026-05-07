from __future__ import annotations

from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse

from app.agents.workflow import workflow
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.schemas import AnalysisRequest, CopilotQuery, UploadResponse
from app.services.analysis_service import analysis_service
from app.services.copilot_service import copilot_service
from app.services.data_service import data_service
from app.services.occ_etl_service import occ_etl_service
from app.services.persistence_service import persistence_service


router = APIRouter()


def _production_df():
    try:
        with SessionLocal() as db:
            persisted = persistence_service.load_dataframe(db)
            if not persisted.empty:
                return persisted
    except Exception:
        pass
    return data_service.dataframe


def _summaries(oil_price: Optional[float] = None, threshold: Optional[float] = None):
    settings = get_settings()
    return analysis_service.analyze_portfolio(
        _production_df(),
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
        try:
            with SessionLocal() as db:
                persistence_service.replace_production_dataset(db, result.dataframe)
        except Exception:
            pass
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UploadResponse(
        rows_ingested=len(result.dataframe),
        wells_loaded=int(result.dataframe["well_id"].nunique()),
        warnings=result.warnings,
    )


@router.post("/ingestion/upload-occ-data", response_model=UploadResponse)
async def upload_occ_data(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No OCC/OTC file uploaded.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded OCC/OTC file is empty.")
    suffix = ".xlsx" if file.filename.lower().endswith((".xlsx", ".xls")) else ".csv"
    try:
        with NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(content)
            tmp.flush()
            result = occ_etl_service.normalize_file(tmp.name)
        data_service._dataframe = result.dataframe
        data_service._warnings = result.warnings
        try:
            with SessionLocal() as db:
                persistence_service.replace_production_dataset(db, result.dataframe)
        except Exception:
            pass
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UploadResponse(
        rows_ingested=len(result.dataframe),
        wells_loaded=int(result.dataframe["well_id"].nunique()),
        warnings=result.warnings,
        data_quality_score=result.quality.score,
        source_type="occ_otc_normalized",
    )


@router.post("/run-analysis")
def run_analysis(request: AnalysisRequest) -> dict[str, object]:
    summaries = _summaries(request.oil_price, request.threshold)
    portfolio = analysis_service.portfolio_summary(summaries)
    return {
        "portfolio": portfolio,
        "agent_telemetry": workflow.orchestrate(
            portfolio,
            summaries,
            analysis_service.basin_summaries(summaries),
            analysis_service.operator_risk(summaries),
        ),
    }


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
    df = _production_df()
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


@router.get("/operators")
def operators():
    return analysis_service.operator_risk(_summaries())


@router.get("/operators/{operator_name}/risk")
def operator_risk(operator_name: str):
    operators = analysis_service.operator_risk(_summaries())
    for operator in operators:
        if operator.operator_name.lower() == operator_name.lower():
            return operator
    raise HTTPException(status_code=404, detail=f"Operator {operator_name} was not found.")


@router.get("/basins")
def basins():
    return analysis_service.basin_summaries(_summaries())


@router.get("/anomalies")
def anomalies():
    return analysis_service.anomaly_records(_production_df())


@router.get("/interventions")
def interventions():
    return workflow.recommendations(_summaries())


@router.get("/portfolio/risk")
def portfolio_risk():
    summaries = _summaries()
    portfolio = analysis_service.portfolio_summary(summaries)
    return workflow.portfolio_risk.run(portfolio)


@router.get("/forecast/confidence")
def forecast_confidence():
    summaries = _summaries()
    return {
        "average_confidence": round(sum(w.confidence_score for w in summaries) / max(len(summaries), 1), 1),
        "low_confidence_wells": [w.well_id for w in summaries if w.confidence_score < 55],
        "model_mix": workflow.forecast_validation.run(summaries)["model_mix"],
    }


@router.get("/copilot/query")
def copilot_get(q: str = Query(min_length=3, max_length=500)):
    summaries = _summaries()
    recs = workflow.recommendations(summaries)
    return copilot_service.query(q, summaries, recs)


@router.post("/copilot/query")
def copilot_post(payload: CopilotQuery):
    summaries = _summaries()
    recs = workflow.recommendations(summaries)
    return copilot_service.query(payload.question, summaries, recs)


@router.get("/executive-summary")
def executive_summary(oil_price: float = Query(default=70.0, gt=0, le=300), threshold: float = Query(default=0.15, gt=0, lt=0.9)):
    summaries = _summaries(oil_price, threshold)
    portfolio = analysis_service.portfolio_summary(summaries)
    return workflow.executive_summary(portfolio, summaries)


@router.get("/executive/report", response_class=HTMLResponse)
def executive_report():
    summaries = _summaries()
    portfolio = analysis_service.portfolio_summary(summaries)
    exec_summary = workflow.executive_summary(portfolio, summaries)
    recs = workflow.recommendations(summaries)[:10]
    rows = "".join(f"<tr><td>{r.well_id}</td><td>{r.priority}</td><td>{r.category}</td><td>{r.estimated_roi}x</td><td>{r.payback_days}</td></tr>" for r in recs)
    return f"""
    <html><head><title>WellGuard AI Executive Report</title>
    <style>body{{font-family:Arial;background:#08111f;color:#e5edf7;padding:32px}}section{{border:1px solid #334155;padding:20px;border-radius:8px;margin:16px 0}}table{{width:100%;border-collapse:collapse}}td,th{{border-bottom:1px solid #334155;padding:10px;text-align:left}}</style>
    </head><body>
    <h1>WellGuard AI Executive Report</h1>
    <section><h2>{exec_summary.headline}</h2><p>{exec_summary.financial_impact}</p><p>Portfolio risk score: {portfolio.portfolio_risk_score}</p></section>
    <section><h2>Recommended Actions</h2><ul>{"".join(f"<li>{a}</li>" for a in exec_summary.recommended_actions)}</ul></section>
    <section><h2>Intervention ROI Queue</h2><table><tr><th>Well</th><th>Priority</th><th>Category</th><th>ROI</th><th>Payback Days</th></tr>{rows}</table></section>
    <p>Decision-support only. Requires qualified engineering and operations review.</p>
    </body></html>
    """


@router.get("/reports/intervention-report.csv")
def intervention_report(oil_price: float = Query(default=70.0, gt=0, le=300), threshold: float = Query(default=0.15, gt=0, lt=0.9)):
    recs = workflow.recommendations(_summaries(oil_price, threshold))
    rows = "well_id,priority,category,rationale,suggested_next_step\n"
    for rec in recs:
        safe = [rec.well_id, rec.priority, rec.category, rec.rationale, rec.suggested_next_step]
        rows += ",".join('"' + item.replace('"', '""') + '"' for item in safe) + "\n"
    return StreamingResponse(iter([rows]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=wellguard_intervention_report.csv"})
