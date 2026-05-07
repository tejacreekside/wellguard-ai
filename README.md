# WellGuard AI

AI-native operational intelligence for oil and gas production.

WellGuard AI detects abnormal production decline, forecasts future output, estimates preventable revenue leakage, ranks wells by urgency, and generates explainable intervention recommendations for operations leaders.

This is built as an AI infrastructure product, not a passive dashboard. The system combines time-series modeling, anomaly detection, financial impact modeling, and deterministic agent workflows to turn production data into operational decisions.

## Business Problem

Oil and gas operators lose material revenue when production decline is not caught early. Production engineers and operations managers often review production reports after value has already leaked through downtime, lift issues, allocation errors, high water handling constraints, or mechanical failures.

WellGuard AI acts as a decision intelligence layer:

- Which wells are declining faster than expected?
- Which wells may underperform next month?
- How much revenue is leaking per day?
- Which wells should be reviewed first?
- What intervention category should operations investigate?
- What should executives do next?

Recommendations are decision-support only and are not engineering approval.

## Product Differentiation

WellGuard AI is not a charting project. It behaves like an operational intelligence engine:

- Fits Arps decline curves per well.
- Scores abnormal decline against expected output.
- Forecasts 3, 6, and 12 month production risk.
- Converts production gaps into dollar leakage.
- Uses modular AI-style agents that work without an LLM.
- Produces executive-ready summaries and intervention queues.
- Handles messy field-style production data without crashing.

## AI Concepts Demonstrated

- Time-series forecasting using Arps decline curves.
- Anomaly detection via expected-vs-actual production variance.
- Agentic workflow design with specialized deterministic agents.
- Financial impact modeling from lost barrels and oil price assumptions.
- Explainable recommendation logic for industrial decision-support.
- Full-stack AI product architecture with FastAPI, React, Plotly, Docker, and tests.

## Architecture

```text
CSV / Synthetic Data
        |
        v
Data Ingestion + Cleaning
        |
        v
Decline Analysis Engine ---- Forecasting Engine
        |                          |
        v                          v
Revenue Leakage Model       Confidence Scoring
        |                          |
        +------------+-------------+
                     v
          WellGuard Agent Workflow
                     |
       +-------------+-------------+
       v                           v
 FastAPI Intelligence API     React Executive Console
```

Agent modules:

- `ProductionMonitoringAgent`
- `DeclineForecastAgent`
- `RevenueLeakageAgent`
- `InterventionAdvisorAgent`
- `ExecutiveSummaryAgent`

The agents receive and return structured data. They do not require an LLM. If an LLM key is later added, it should only polish summaries, not replace the deterministic operating logic.

## Project Structure

```text
wellguard-ai/
  backend/
    app/
      main.py
      api/
      core/
      models/
      services/
      agents/
      ml/
      data/
      utils/
    tests/
    requirements.txt
    Dockerfile
  frontend/
    src/
    package.json
    Dockerfile
  data/
    sample_production_data.csv
  reports/
  docker-compose.yml
  README.md
```

## Dataset

The included seed dataset contains 30 Oklahoma-style wells across:

- Operators: Kirkpatrick Oil, Crawley Petroleum, Comanche Resources, Mewbourne Oil, Casillas Petroleum
- Basins: SCOOP, STACK, Anadarko
- Formations: Woodford, Springer, Meramec, Osage

It includes 36 months of production history with realistic decline behavior and injected anomalies such as sudden production drops, high water conditions, missing dates, duplicate rows, negative values, zero production months, and inactive wells.

Generate a fresh sample:

```bash
cd backend
python3 -m app.data.sample_generator
```

## Run With Docker

```bash
docker-compose up --build
```

Services:

- Backend API: `http://localhost:8000`
- Frontend dashboard: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

## Local Development

Backend:

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /health`
- `POST /upload-production-data`
- `POST /run-analysis`
- `GET /portfolio/summary`
- `GET /wells`
- `GET /wells/{well_id}/analysis`
- `GET /wells/{well_id}/forecast`
- `GET /recommendations`
- `GET /executive-summary`
- `GET /reports/intervention-report.csv`

Upload CSV columns:

```text
well_id, operator_name, basin, formation, production_date, oil_bbl, gas_mcf, water_bbl, status
```

## Decline Analysis

WellGuard AI fits the Arps decline curve per well:

```text
q(t) = qi / (1 + b * Di * t)^(1/b)
```

It compares latest actual oil production against expected production and flags wells below expected output by a configurable threshold. Default threshold is 15%.

Revenue leakage:

```text
lost_bbl_per_day * oil_price
```

Default oil price is `$70/bbl`.

## Recommendation Logic

Rules are explainable and deterministic:

- High water plus production drop: artificial lift review.
- Sudden drop after stable production: workover candidate.
- Flat zero production: shut-in / inactive review.
- Noisy or missing data: data quality review.
- Gradual decline close to expected: normal decline / no action.

Every recommendation includes the statement that the output is decision-support and not engineering approval.

## Dashboard

The React dashboard includes:

- Portfolio Health Score
- Daily revenue leakage
- 30-day exposure
- Top bleeding wells
- Actual vs expected vs forecast decline chart
- Risk score by well
- Operator, basin, and formation filters
- AI Executive Brief
- Intervention Priority Table
- Downloadable CSV report
- CSV upload workflow

Screenshot targets after running locally:

- Overview KPI cards and AI Executive Brief
- Well-level decline chart
- Intervention Priority Table
- API docs at `/docs`

## Testing

```bash
cd backend
python3 -m pytest
```

Current coverage includes:

- Data validation and messy-data cleanup
- Decline curve fitting
- Abnormal decline detection
- Revenue leakage calculation
- Recommendation decision-support logic

Frontend build:

```bash
cd frontend
npm run build
```

## Recruiter Angle

WellGuard AI demonstrates applied AI engineering beyond prompt wrapping:

- Production-grade FastAPI backend architecture.
- Modular ML and agent services.
- Industrial time-series modeling.
- Financial impact modeling.
- Explainable AI recommendations.
- Executive-grade frontend product thinking.
- Dockerized full-stack delivery.

LinkedIn framing:

> Built an AI-native operational intelligence platform that detects abnormal production decline, forecasts revenue leakage, and generates explainable intervention recommendations for energy operators.
