import React from "react";
import ReactDOM from "react-dom/client";
import { Activity, AlertTriangle, BarChart3, BrainCircuit, Download, Factory, FileUp, Gauge, GitBranch, Map, Network, Send, ShieldCheck, TrendingDown } from "lucide-react";
import Plot from "react-plotly.js";
import { api } from "./api";
import type { AnomalyRecord, BasinSummary, CopilotResponse, ExecutiveSummary, OperatorRisk, PortfolioSummary, Recommendation, WellAnalysis, WellSummary } from "./types";
import "./styles.css";

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function App() {
  const [portfolio, setPortfolio] = React.useState<PortfolioSummary | null>(null);
  const [wells, setWells] = React.useState<WellSummary[]>([]);
  const [recommendations, setRecommendations] = React.useState<Recommendation[]>([]);
  const [executive, setExecutive] = React.useState<ExecutiveSummary | null>(null);
  const [operatorRisk, setOperatorRisk] = React.useState<OperatorRisk[]>([]);
  const [basinRisk, setBasinRisk] = React.useState<BasinSummary[]>([]);
  const [anomalies, setAnomalies] = React.useState<AnomalyRecord[]>([]);
  const [copilotQuestion, setCopilotQuestion] = React.useState("Which wells are highest risk?");
  const [copilotAnswer, setCopilotAnswer] = React.useState<CopilotResponse | null>(null);
  const [selectedWell, setSelectedWell] = React.useState<string>("");
  const [analysis, setAnalysis] = React.useState<WellAnalysis | null>(null);
  const [operator, setOperator] = React.useState("All");
  const [basin, setBasin] = React.useState("All");
  const [formation, setFormation] = React.useState("All");
  const [error, setError] = React.useState("");

  const load = React.useCallback(async () => {
    setError("");
    const [p, w, r, e, o, b, a] = await Promise.allSettled([api.portfolio(), api.wells(), api.recommendations(), api.executive(), api.operators(), api.basins(), api.anomalies()]);

    if (p.status === "fulfilled") setPortfolio(p.value);
    if (w.status === "fulfilled") {
      setWells(w.value);
      setSelectedWell((current) => current || w.value[0]?.well_id || "");
    }
    if (r.status === "fulfilled") setRecommendations(r.value);
    if (e.status === "fulfilled") setExecutive(e.value);
    if (o.status === "fulfilled") setOperatorRisk(o.value);
    if (b.status === "fulfilled") setBasinRisk(b.value);
    if (a.status === "fulfilled") setAnomalies(a.value);

    const failures = [p, w, r, e, o, b, a].filter((result) => result.status === "rejected");
    if (failures.length) {
      const firstFailure = failures[0] as PromiseRejectedResult;
      setError(firstFailure.reason instanceof Error ? firstFailure.reason.message : "Some WellGuard AI data did not load.");
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  React.useEffect(() => {
    if (!selectedWell) return;
    api.wellAnalysis(selectedWell).then(setAnalysis).catch((err) => setError(err.message));
  }, [selectedWell]);

  const filtered = wells.filter((well) => {
    return (operator === "All" || well.operator_name === operator) && (basin === "All" || well.basin === basin) && (formation === "All" || well.formation === formation);
  });
  const operators = ["All", ...Array.from(new Set(wells.map((w) => w.operator_name)))];
  const basins = ["All", ...Array.from(new Set(wells.map((w) => w.basin)))];
  const formations = ["All", ...Array.from(new Set(wells.map((w) => w.formation)))];

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await api.upload(file);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    }
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><ShieldCheck size={26} />WellGuard AI</div>
        <nav>
          <span><Gauge size={18} /> Overview</span>
          <span><TrendingDown size={18} /> Decline Intelligence</span>
          <span><BrainCircuit size={18} /> Agent Brief</span>
          <span><Map size={18} /> Basin Intelligence</span>
          <span><Network size={18} /> Architecture</span>
          <span><Factory size={18} /> Intervention Queue</span>
        </nav>
        <label className="upload">
          <FileUp size={18} />
          Upload CSV
          <input type="file" accept=".csv" onChange={handleUpload} />
        </label>
        <a className="download" href={api.reportUrl()}><Download size={18} /> CSV Report</a>
        <a className="download" href={api.executiveReportUrl()} target="_blank"><Download size={18} /> Executive Report</a>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Industrial AI Operations Console</p>
            <h1>Production decline intelligence and revenue leakage command center</h1>
          </div>
          <div className="filters">
            <select value={operator} onChange={(e) => setOperator(e.target.value)}>{operators.map((x) => <option key={x}>{x}</option>)}</select>
            <select value={basin} onChange={(e) => setBasin(e.target.value)}>{basins.map((x) => <option key={x}>{x}</option>)}</select>
            <select value={formation} onChange={(e) => setFormation(e.target.value)}>{formations.map((x) => <option key={x}>{x}</option>)}</select>
          </div>
        </header>

        {error && <div className="error"><AlertTriangle size={18} />{error}</div>}

        <section className="kpis">
          <Kpi icon={<ShieldCheck />} label="Portfolio Health" value={`${portfolio?.portfolio_health_score ?? "--"}/100`} />
          <Kpi icon={<Activity />} label="Flagged Wells" value={`${portfolio?.flagged_well_count ?? "--"}/${portfolio?.well_count ?? "--"}`} />
          <Kpi icon={<TrendingDown />} label="Daily Leakage" value={formatMoney(portfolio?.total_daily_revenue_leakage ?? 0)} />
          <Kpi icon={<BarChart3 />} label="Annual Leakage" value={formatMoney(portfolio?.estimated_annual_leakage ?? 0)} />
          <Kpi icon={<Gauge />} label="Portfolio Risk" value={`${portfolio?.portfolio_risk_score ?? "--"}/100`} />
          <Kpi icon={<Activity />} label="Stability" value={`${portfolio?.production_stability_score ?? "--"}/100`} />
          <Kpi icon={<Factory />} label="Operator Efficiency" value={`${portfolio?.operator_efficiency_index ?? "--"}/100`} />
          <Kpi icon={<TrendingDown />} label="ROI Potential" value={`${portfolio?.intervention_roi_potential ?? "--"}x`} />
        </section>

        <section className="grid two">
          <article className="panel brief">
            <div className="panel-title"><BrainCircuit size={20} />AI Executive Brief</div>
            <h2>{executive?.headline}</h2>
            {executive?.portfolio_takeaways.map((item) => <p key={item}>{item}</p>)}
            <strong>{executive?.financial_impact}</strong>
          </article>
          <article className="panel">
            <div className="panel-title"><TrendingDown size={20} />Revenue Leakage</div>
            <Plot
              data={[{ type: "bar", x: filtered.slice(0, 10).map((w) => w.well_id), y: filtered.slice(0, 10).map((w) => w.revenue_leakage_daily), marker: { color: "#f97316" } }]}
              layout={plotLayout("Estimated $/day leakage")}
              config={{ displayModeBar: false, responsive: true }}
              className="plot"
            />
          </article>
        </section>

        <section className="grid two">
          <article className="panel">
            <div className="panel-title"><Map size={20} />Geographic Well Risk Map</div>
            <Plot
              data={[{ type: "scattermap", lat: filtered.map((w) => w.latitude), lon: filtered.map((w) => w.longitude), text: filtered.map((w) => `${w.well_id} risk ${w.risk_score}`), marker: { size: filtered.map((w) => Math.max(8, w.risk_score / 5)), color: filtered.map((w) => w.risk_score), colorscale: "Portland", showscale: true } }]}
              layout={{ ...plotLayout("Oklahoma well risk"), map: { style: "open-street-map", zoom: 5.4, center: { lat: 35.6, lon: -97.7 } } }}
              config={{ displayModeBar: false, responsive: true }}
              className="plot"
            />
          </article>
          <article className="panel">
            <div className="panel-title"><AlertTriangle size={20} />AI Anomaly Timeline</div>
            <Plot
              data={[{ type: "scatter", mode: "markers", x: anomalies.map((a) => a.production_date), y: anomalies.map((a) => a.well_id), text: anomalies.map((a) => `${a.anomaly_type}: ${a.explanation}`), marker: { size: anomalies.map((a) => Math.max(8, a.severity / 5)), color: anomalies.map((a) => a.severity), colorscale: "YlOrRd" } }]}
              layout={plotLayout("Anomaly severity by month")}
              config={{ displayModeBar: false, responsive: true }}
              className="plot"
            />
          </article>
        </section>

        <section className="grid two">
          <article className="panel">
            <div className="panel-title"><Factory size={20} />Operator Comparison</div>
            <Plot
              data={[{ type: "bar", x: operatorRisk.map((o) => o.operator_name), y: operatorRisk.map((o) => o.daily_revenue_leakage), marker: { color: "#38bdf8" } }]}
              layout={plotLayout("Operator leakage exposure")}
              config={{ displayModeBar: false, responsive: true }}
              className="plot"
            />
          </article>
          <article className="panel">
            <div className="panel-title"><BarChart3 size={20} />Basin Benchmark Heatmap</div>
            <Plot
              data={[{ type: "heatmap", x: basinRisk.map((b) => b.basin), y: ["Risk", "Leakage", "Stability"], z: [basinRisk.map((b) => b.average_risk_score), basinRisk.map((b) => b.daily_revenue_leakage / 100), basinRisk.map((b) => b.production_stability_score)], colorscale: "Viridis" }]}
              layout={plotLayout("Basin intelligence")}
              config={{ displayModeBar: false, responsive: true }}
              className="plot"
            />
          </article>
        </section>

        <section className="grid two analysis-grid">
          <article className="panel">
            <div className="panel-title"><Activity size={20} />Well-Level Decline</div>
            <select className="well-picker" value={selectedWell} onChange={(e) => setSelectedWell(e.target.value)}>
              {filtered.map((w) => <option key={w.well_id}>{w.well_id}</option>)}
            </select>
            {analysis && <DeclinePlot analysis={analysis} />}
          </article>
          <article className="panel">
            <div className="panel-title"><Gauge size={20} />Risk Score by Well</div>
            <Plot
              data={[{ type: "bar", orientation: "h", x: filtered.slice(0, 12).map((w) => w.risk_score), y: filtered.slice(0, 12).map((w) => w.well_id), marker: { color: filtered.slice(0, 12).map((w) => w.risk_score >= 65 ? "#ef4444" : "#22c55e") } }]}
              layout={plotLayout("Risk score")}
              config={{ displayModeBar: false, responsive: true }}
              className="plot"
            />
          </article>
        </section>

        <section className="grid two">
          <article className="panel copilot">
            <div className="panel-title"><BrainCircuit size={20} />AI Operational Copilot</div>
            <div className="copilot-input">
              <input value={copilotQuestion} onChange={(e) => setCopilotQuestion(e.target.value)} />
              <button onClick={async () => setCopilotAnswer(await api.copilot(copilotQuestion))}><Send size={18} /></button>
            </div>
            <p>{copilotAnswer?.answer ?? "Ask about highest risk wells, abnormal decline in a basin, operator leakage, interventions, or next-quarter forecasts."}</p>
            <small>{copilotAnswer ? `Confidence ${copilotAnswer.confidence_score}/100 using ${copilotAnswer.mode}` : "Deterministic RAG fallback, OpenAI optional."}</small>
          </article>
          <article className="panel architecture">
            <div className="panel-title"><GitBranch size={20} />AI Pipeline Architecture</div>
            <div className="pipeline">
              <span>OCC/OTC ETL</span><span>Quality Scoring</span><span>Decline Models</span><span>Anomaly Engine</span><span>Agent Orchestrator</span><span>Copilot RAG</span>
            </div>
            <p>Forecasting, anomaly detection, intervention ROI, and executive intelligence run as structured services behind FastAPI.</p>
          </article>
        </section>

        <section className="panel">
          <div className="panel-title"><AlertTriangle size={20} />Intervention Priority Table</div>
          <table>
            <thead><tr><th>Well</th><th>Priority</th><th>Category</th><th>Risk</th><th>Leakage</th><th>ROI</th><th>Rationale</th></tr></thead>
            <tbody>
              {recommendations.slice(0, 12).map((rec) => {
                const well = wells.find((w) => w.well_id === rec.well_id);
                return <tr key={rec.well_id}><td>{rec.well_id}</td><td><span className={`pill ${rec.priority.toLowerCase()}`}>{rec.priority}</span></td><td>{rec.category}</td><td>{well?.risk_score}</td><td>{formatMoney(well?.revenue_leakage_daily ?? 0)}</td><td>{rec.estimated_roi}x</td><td>{rec.rationale}</td></tr>;
              })}
            </tbody>
          </table>
          <p className="notice">{recommendations[0]?.decision_support_notice}</p>
        </section>
      </section>
    </main>
  );
}

function Kpi({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <article className="kpi"><span>{icon}</span><p>{label}</p><strong>{value}</strong></article>;
}

function DeclinePlot({ analysis }: { analysis: WellAnalysis }) {
  const historyDates = analysis.history.map((h) => h.production_date);
  const forecastDates = analysis.forecast.map((h) => h.production_date);
  return (
    <Plot
      data={[
        { type: "scatter", mode: "lines+markers", name: "Actual", x: historyDates, y: analysis.history.map((h) => h.oil_bbl), line: { color: "#38bdf8", width: 3 } },
        { type: "scatter", mode: "lines", name: "Expected", x: historyDates, y: analysis.history.map((h) => h.expected_oil_bbl), line: { color: "#22c55e", width: 3 } },
        { type: "scatter", mode: "lines", name: "Forecast", x: forecastDates, y: analysis.forecast.map((h) => h.forecast_oil_bbl), line: { color: "#f97316", dash: "dot", width: 3 } },
      ]}
      layout={plotLayout(`${analysis.well.well_id}: actual vs expected vs forecast`)}
      config={{ displayModeBar: false, responsive: true }}
      className="plot tall"
    />
  );
}

function plotLayout(title: string) {
  return {
    title: { text: title, font: { color: "#dbeafe", size: 14 } },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(9,14,25,0.75)",
    font: { color: "#cbd5e1" },
    margin: { l: 52, r: 20, t: 44, b: 48 },
    autosize: true,
    xaxis: { gridcolor: "rgba(148,163,184,0.14)" },
    yaxis: { gridcolor: "rgba(148,163,184,0.14)" },
  };
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
