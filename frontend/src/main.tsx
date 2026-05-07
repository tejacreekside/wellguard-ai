import React from "react";
import ReactDOM from "react-dom/client";
import { Activity, AlertTriangle, BarChart3, BrainCircuit, Download, Factory, FileUp, Gauge, ShieldCheck, TrendingDown } from "lucide-react";
import Plot from "react-plotly.js";
import { api } from "./api";
import type { ExecutiveSummary, PortfolioSummary, Recommendation, WellAnalysis, WellSummary } from "./types";
import "./styles.css";

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function App() {
  const [portfolio, setPortfolio] = React.useState<PortfolioSummary | null>(null);
  const [wells, setWells] = React.useState<WellSummary[]>([]);
  const [recommendations, setRecommendations] = React.useState<Recommendation[]>([]);
  const [executive, setExecutive] = React.useState<ExecutiveSummary | null>(null);
  const [selectedWell, setSelectedWell] = React.useState<string>("");
  const [analysis, setAnalysis] = React.useState<WellAnalysis | null>(null);
  const [operator, setOperator] = React.useState("All");
  const [basin, setBasin] = React.useState("All");
  const [formation, setFormation] = React.useState("All");
  const [error, setError] = React.useState("");

  const load = React.useCallback(async () => {
    try {
      setError("");
      const [p, w, r, e] = await Promise.all([api.portfolio(), api.wells(), api.recommendations(), api.executive()]);
      setPortfolio(p);
      setWells(w);
      setRecommendations(r);
      setExecutive(e);
      setSelectedWell((current) => current || w[0]?.well_id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load WellGuard AI data.");
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
          <span><Factory size={18} /> Intervention Queue</span>
        </nav>
        <label className="upload">
          <FileUp size={18} />
          Upload CSV
          <input type="file" accept=".csv" onChange={handleUpload} />
        </label>
        <a className="download" href={api.reportUrl()}><Download size={18} /> CSV Report</a>
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
          <Kpi icon={<BarChart3 />} label="30-Day Exposure" value={formatMoney(portfolio?.estimated_30_day_leakage ?? 0)} />
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

        <section className="panel">
          <div className="panel-title"><AlertTriangle size={20} />Intervention Priority Table</div>
          <table>
            <thead><tr><th>Well</th><th>Priority</th><th>Category</th><th>Risk</th><th>Leakage</th><th>Rationale</th></tr></thead>
            <tbody>
              {recommendations.slice(0, 12).map((rec) => {
                const well = wells.find((w) => w.well_id === rec.well_id);
                return <tr key={rec.well_id}><td>{rec.well_id}</td><td><span className={`pill ${rec.priority.toLowerCase()}`}>{rec.priority}</span></td><td>{rec.category}</td><td>{well?.risk_score}</td><td>{formatMoney(well?.revenue_leakage_daily ?? 0)}</td><td>{rec.rationale}</td></tr>;
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
