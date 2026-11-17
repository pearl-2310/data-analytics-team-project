import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, AreaChart, Area, BarChart, Bar, ReferenceLine,
} from "recharts";
import {
  LayoutDashboard, TrendingUp, ChartNoAxesCombined, FlaskConical,
  Database, Download, CalendarDays, Activity, Menu,
  GitCompareArrows, RefreshCw, AlertCircle, CheckCircle2,
} from "lucide-react";
import "./App.css";

const API_BASE = "http://127.0.0.1:5000";

const navigation = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Revenue Analysis", icon: TrendingUp },
  { label: "Sales Analysis", icon: ChartNoAxesCombined },
  { label: "Causal Impact", icon: GitCompareArrows },
  { label: "Placebo Tests", icon: FlaskConical },
  { label: "Data Explorer", icon: Database },
];

function rowsFrom(payload) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];
  for (const key of ["data", "results", "rows", "records", "weights", "summary", "placebo"]) {
    if (Array.isArray(payload[key])) return payload[key];
  }
  return [];
}

function firstValue(obj, keys, fallback = null) {
  if (!obj) return fallback;
  for (const key of keys) {
    if (obj[key] !== undefined && obj[key] !== null && obj[key] !== "") return obj[key];
  }
  return fallback;
}

function numberValue(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function formatNumber(value, digits = 2) {
  const n = numberValue(value);
  return n === null ? "—" : n.toLocaleString(undefined, { maximumFractionDigits: digits });
}

// Normalize date values to YYYY-MM-DD without timezone shifting CSV dates.
function dateKey(value) {
  if (!value) return "";
  const text = String(value).trim();
  const direct = text.match(/^(\d{4}-\d{2}-\d{2})/);
  if (direct) return direct[1];
  const parsed = new Date(text);
  if (Number.isNaN(parsed.getTime())) return text.slice(0, 10);
  return `${parsed.getFullYear()}-${String(parsed.getMonth() + 1).padStart(2, "0")}-${String(parsed.getDate()).padStart(2, "0")}`;
}

function formatDate(value) {
  const key = dateKey(value);
  if (!key) return "—";
  const parts = key.split("-");
  if (parts.length === 3 && parts.every(Boolean)) {
    const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    return Number.isNaN(d.getTime())
      ? key
      : d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
  }
  return String(value);
}

function normalizeOutcomeRows(rows) {
  return rows.map((row) => {
    const rawDate = firstValue(row, ["Date", "date", "DATE", "ds"], "");
    const actual = numberValue(firstValue(row, ["Actual", "actual", "Actual_Value", "actual_value"], null));
    const synthetic = numberValue(firstValue(row, ["Synthetic", "synthetic", "Synthetic_Value", "synthetic_value"], null));
    const gapRaw = firstValue(row, ["Gap", "gap", "Effect", "effect"], null);
    return {
      ...row,
      date: dateKey(rawDate),
      actual,
      synthetic,
      gap: numberValue(gapRaw) ?? (actual !== null && synthetic !== null ? actual - synthetic : null),
      period: firstValue(row, ["Period", "period"], ""),
      outcome: firstValue(row, ["Outcome", "outcome"], ""),
    };
  }).filter((row) => row.date && (row.actual !== null || row.synthetic !== null));
}

function MetricCard({ title, value, subtitle, icon: Icon, accent }) {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <span>{title}</span>
        <span className={`metric-icon ${accent}`}><Icon size={19} /></span>
      </div>
      <h2>{value}</h2>
      <p>{subtitle}</p>
    </div>
  );
}

function ChartCard({ title, subtitle, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <div><h3>{title}</h3><p>{subtitle}</p></div>
      </div>
      {children}
    </section>
  );
}

function DataTable({ rows, emptyText = "No results returned by the API yet." }) {
  if (!rows?.length) return <div className="empty-state">{emptyText}</div>;
  const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  return (
    <div className="table-scroll">
      <table className="results-table">
        <thead><tr>{columns.map((col) => <th key={col}>{col.replaceAll("_", " ")}</th>)}</tr></thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((col) => {
                const value = row[col];
                return <td key={col}>{value === null || value === undefined ? "—" : typeof value === "number" ? formatNumber(value, 4) : String(value)}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DateSelect({ value, dates, onChange, label = "Intervention date" }) {
  return (
    <label className="date-select-wrap intervention-date-control">
      <CalendarDays size={17} />
      <span className="date-select-label">{label}</span>
      <select aria-label={label} value={value} onChange={(event) => onChange(event.target.value)}>
        {dates.map((date) => <option key={date} value={date}>{formatDate(date)}</option>)}
      </select>
    </label>
  );
}

function OutcomeAnalysis({ rows, label, subtitle, selectedDate, availableDates, onDateChange }) {
  const visibleRows = selectedDate ? rows.filter((row) => dateKey(row.date) === selectedDate) : rows;
  const chartRows = visibleRows.map((row) => ({ ...row, date: formatDate(row.date) }));

  return (
    <ChartCard
      title={`${label}: Actual vs Synthetic`}
      subtitle={`${subtitle}${selectedDate ? ` · Selected date: ${formatDate(selectedDate)}` : " · All dates"}`}
    >
      <div className="date-data-toolbar">
        <div className="date-data-copy">
          <span className="date-data-eyebrow">CHART DATE FILTER</span>
          <h4>Choose a date</h4>
          <p>Changing the date updates the chart and records automatically.</p>
        </div>
        <div className="date-data-controls">
          <DateSelect value={selectedDate} dates={availableDates} onChange={onDateChange} label={`${label} date`} />
          <button type="button" className="hide-data-button" onClick={() => onDateChange("")}>Show All</button>
        </div>
      </div>

      {chartRows.length ? (
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={chartRows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" minTickGap={30} />
            <YAxis />
            <Tooltip formatter={(value) => formatNumber(value)} />
            <Legend />
            <Line dataKey="actual" name={`Actual ${label.toLowerCase()}`} stroke="#5965e9" dot={chartRows.length === 1} activeDot={{ r: 6 }} />
            <Line dataKey="synthetic" name={`Synthetic ${label.toLowerCase()}`} stroke="#20b894" dot={chartRows.length === 1} activeDot={{ r: 6 }} />
            <Line dataKey="gap" name="Gap" stroke="#f59e0b" dot={chartRows.length === 1} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      ) : <div className="empty-state">No {label.toLowerCase()} results for this date.</div>}

      <div className="filtered-data-result">
        <div className="filtered-data-heading">
          <div>
            <strong>{selectedDate ? formatDate(selectedDate) : "All dates"}</strong>
            <span>{visibleRows.length} matching record{visibleRows.length === 1 ? "" : "s"}</span>
          </div>
        </div>
        <DataTable rows={visibleRows} emptyText="No records are available for the selected date." />
      </div>
    </ChartCard>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState("Overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState("");
  const [apiOnline, setApiOnline] = useState(false);

  const [summaryRows, setSummaryRows] = useState([]);
  const [revenueRows, setRevenueRows] = useState([]);
  const [salesRows, setSalesRows] = useState([]);
  const [weightRowsRaw, setWeightRowsRaw] = useState([]);
  const [placeboRows, setPlaceboRows] = useState([]);
  const [sourceRows, setSourceRows] = useState([]);
  const [interventionDate, setInterventionDate] = useState("2025-03-10");
  const [revenueDate, setRevenueDate] = useState("");
  const [salesDate, setSalesDate] = useState("");

  const loadResults = async () => {
    setLoading(true);
    setApiError("");
    try {
      const paths = ["/api/summary", "/api/revenue", "/api/sales", "/api/weights", "/api/placebo", "/api/data"];
      const responses = await Promise.allSettled(paths.map((path) => axios.get(`${API_BASE}${path}`, { timeout: 15000 })));
      const successful = responses.filter((r) => r.status === "fulfilled");
      if (!successful.length) throw new Error("Could not reach Flask API. Start backend/app.py on port 5000.");

      const byPath = {};
      responses.forEach((result, i) => {
        if (result.status === "fulfilled") byPath[paths[i]] = result.value.data;
      });
      const nextRevenue = normalizeOutcomeRows(rowsFrom(byPath["/api/revenue"]));
      const nextSales = normalizeOutcomeRows(rowsFrom(byPath["/api/sales"]));
      setSummaryRows(rowsFrom(byPath["/api/summary"]));
      setRevenueRows(nextRevenue);
      setSalesRows(nextSales);
      setWeightRowsRaw(rowsFrom(byPath["/api/weights"]));
      setPlaceboRows(rowsFrom(byPath["/api/placebo"]));
      setSourceRows(rowsFrom(byPath["/api/data"]));
      setApiOnline(true);

      const allDates = [...new Set([...nextRevenue, ...nextSales].map((row) => row.date))].sort();
      if (allDates.length) {
        setInterventionDate((current) => allDates.includes(current) ? current : allDates[0]);
      }
      const failed = responses.map((result, i) => result.status === "rejected" ? paths[i] : null).filter(Boolean);
      if (failed.length) setApiError(`Some result files could not be loaded: ${failed.join(", ")}. Check your backend results folder.`);
    } catch (error) {
      setApiOnline(false);
      setApiError(error?.message || "Unable to load analysis results.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadResults(); }, []);

  const availableDates = useMemo(() => [...new Set([...revenueRows, ...salesRows].map((row) => dateKey(row.date)).filter(Boolean))].sort(), [revenueRows, salesRows]);
  const revenueData = useMemo(() => revenueRows.map((row) => ({ ...row, date: formatDate(row.date) })), [revenueRows]);
  const salesData = useMemo(() => salesRows.map((row) => ({ ...row, date: formatDate(row.date) })), [salesRows]);

  const selectedRevenue = revenueRows.filter((row) => dateKey(row.date) === interventionDate);
  const selectedSales = salesRows.filter((row) => dateKey(row.date) === interventionDate);
  const selectedRevenueOne = selectedRevenue[0] || {};
  const selectedSalesOne = selectedSales[0] || {};

  const donorData = useMemo(() => weightRowsRaw.map((row) => {
    const region = firstValue(row, ["Region_ID", "Region", "region", "Donor_Region", "donor_region", "Unit"], "Unknown region");
    const rawWeight = numberValue(firstValue(row, ["Weight", "weight", "Synthetic_Control_Weight", "synthetic_control_weight"], 0)) ?? 0;
    const weight = Math.abs(rawWeight) <= 1 ? rawWeight * 100 : rawWeight;
    return { region: String(region).replaceAll("_", " "), weight };
  }).filter((row) => row.region !== "Unknown region" || row.weight !== 0), [weightRowsRaw]);

  const avgGap = useMemo(() => {
    const candidates = summaryRows.map((row) => numberValue(firstValue(row, ["Average_Post_Treatment_Gap", "average_post_treatment_gap"], null))).filter((v) => v !== null);
    return candidates.length ? candidates[0] : null;
  }, [summaryRows]);

  const donorCount = donorData.length;
  const outcomeCount = summaryRows.length || ((revenueRows.length ? 1 : 0) + (salesRows.length ? 1 : 0));

  const downloadRows = (rows, filename) => {
    if (!rows?.length) {
      window.alert("There is no loaded data to export yet. Check API connection and result CSV files.");
      return;
    }
    const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
    const escape = (value) => `"${(value === null || value === undefined ? "" : String(value)).replaceAll('"', '""')}"`;
    const csv = [columns.map(escape).join(","), ...rows.map((row) => columns.map((col) => escape(row[col])).join(","))].join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const exportCurrent = () => {
    if (activePage === "Revenue Analysis") return downloadRows(revenueRows, "revenue_synthetic_control_results.csv");
    if (activePage === "Sales Analysis") return downloadRows(salesRows, "sales_synthetic_control_results.csv");
    if (activePage === "Placebo Tests") return downloadRows(placeboRows, "placebo_test_results.csv");
    if (activePage === "Data Explorer") return downloadRows(sourceRows, "analysis_ready_data.csv");
    if (activePage === "Causal Impact") return downloadRows(summaryRows, "synthetic_control_summary.csv");
    return downloadRows([...revenueRows, ...salesRows], "synthetic_control_results.csv");
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="brand"><div className="brand-logo">SC</div><div><h2>SynthControl</h2><span>CAUSAL ANALYTICS</span></div></div>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="nav-list">
          {navigation.map(({ label, icon: Icon }) => (
            <button key={label} className={`nav-item ${activePage === label ? "active" : ""}`} onClick={() => { setActivePage(label); setSidebarOpen(false); }}>
              <Icon size={19} /><span>{label}</span>{activePage === label && <span className="active-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="project-status"><span className="status-dot" /><div><strong>Analysis workspace</strong><small>{apiOnline ? "Connected to Python results" : "Waiting for API"}</small></div></div>
          <button className="nav-item settings-item" onClick={loadResults}><RefreshCw size={19} /><span>Refresh results</span></button>
          <div className="profile"><div className="avatar">CA</div><div><strong>Causal Analysis</strong><small>Research project</small></div></div>
        </div>
      </aside>

      {sidebarOpen && <button className="sidebar-overlay" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}

      <main className="main-content">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="Toggle navigation"><Menu size={22} /></button>
          <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-separator">/</span><strong>{activePage}</strong></div>
          <div className="topbar-right">
            <span className="status-badge"><span className="status-dot" />{apiOnline ? "API connected" : "API disconnected"}</span>
            <div className="top-avatar">CA</div>
          </div>
        </header>

        <div className="page-content">
          <section className="page-title-row">
            <div>
              <div className="eyebrow"><Activity size={15} /> CAUSAL INFERENCE PLATFORM</div>
              <h1>{activePage}</h1>
              <p className="page-description">Real results from your Python synthetic control analysis.</p>
            </div>
            <button className="export-button" onClick={exportCurrent}><Download size={17} /> Export results CSV</button>
          </section>

          <section className="filter-row">
            <DateSelect value={interventionDate} dates={availableDates} onChange={setInterventionDate} />
            <div className="filter-divider" />
            <div className="filter-item"><span className="filter-dot" /><span>Treated region:</span><strong>Region_1</strong></div>
            <div className="filter-divider" />
            <div className="filter-item"><Database size={17} /><span>Method:</span><strong>Synthetic Control</strong></div>
          </section>

          {activePage === "Overview" && <>
            <section className="metrics-grid">
              <MetricCard title="Treated Region" value="Region_1" subtitle="Selected intervention region" icon={Activity} accent="purple" />
              <MetricCard title="Donor Regions" value={donorCount ? String(donorCount) : "—"} subtitle="Loaded from model weights" icon={Database} accent="blue" />
              <MetricCard title="Intervention Date" value={formatDate(interventionDate)} subtitle="Selected intervention date" icon={CalendarDays} accent="orange" />
              <MetricCard title="Outcomes" value={String(outcomeCount).padStart(2, "0")} subtitle="Loaded analysis outcomes" icon={ChartNoAxesCombined} accent="green" />
            </section>

            <section className="chart-grid">
              <ChartCard title="Revenue: Actual vs Synthetic" subtitle="Revenue proxy · Real synthetic-control output" className="large-chart">
                {revenueData.length ? <ResponsiveContainer width="100%" height={290}>
                  <LineChart data={revenueData} margin={{ top: 12, right: 12, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f5" />
                    <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fill: "#8791a5", fontSize: 11 }} minTickGap={28} />
                    <YAxis tickLine={false} axisLine={false} tick={{ fill: "#8791a5", fontSize: 11 }} tickFormatter={(v) => Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(0)}k` : v} width={48} />
                    <Tooltip formatter={(v) => formatNumber(v)} /><Legend />
                    <ReferenceLine x={formatDate(interventionDate)} stroke="#ef9d42" strokeDasharray="5 5" label="Intervention" />
                    <Line type="monotone" dataKey="actual" name="Actual revenue" stroke="#5965e9" strokeWidth={2.5} dot={false} connectNulls />
                    <Line type="monotone" dataKey="synthetic" name="Synthetic revenue" stroke="#20b894" strokeWidth={2.5} dot={false} connectNulls />
                  </LineChart>
                </ResponsiveContainer> : <div className="empty-state">{loading ? "Loading revenue output…" : "No revenue rows received. Check /api/revenue."}</div>}
              </ChartCard>
              <ChartCard title="Sales Volume" subtitle="Actual vs synthetic · Real model output">
                {salesData.length ? <ResponsiveContainer width="100%" height={330}>
                  <AreaChart data={salesData} margin={{ top: 15, right: 5, left: -15, bottom: 0 }}>
                    <defs><linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7c70f5" stopOpacity={0.25} /><stop offset="95%" stopColor="#7c70f5" stopOpacity={0.01} /></linearGradient></defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f5" />
                    <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fill: "#8791a5", fontSize: 10 }} minTickGap={28} />
                    <YAxis tickLine={false} axisLine={false} tick={{ fill: "#8791a5", fontSize: 11 }} />
                    <Tooltip formatter={(v) => formatNumber(v)} /><Legend />
                    <ReferenceLine x={formatDate(interventionDate)} stroke="#ef9d42" strokeDasharray="5 5" label="Intervention" />
                    <Area type="monotone" dataKey="actual" name="Actual sales" stroke="#7c70f5" fill="url(#salesFill)" strokeWidth={2.3} />
                    <Line type="monotone" dataKey="synthetic" name="Synthetic sales" stroke="#20b894" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer> : <div className="empty-state">{loading ? "Loading sales output…" : "No sales rows received. Check /api/sales."}</div>}
              </ChartCard>
            </section>

            <ChartCard title={`Data for ${formatDate(interventionDate)}`} subtitle="Selected date values update when the intervention date changes">
              <section className="metrics-grid selected-date-metrics">
                <MetricCard title="Actual Revenue" value={formatNumber(selectedRevenueOne.actual)} subtitle={formatDate(interventionDate)} icon={TrendingUp} accent="purple" />
                <MetricCard title="Synthetic Revenue" value={formatNumber(selectedRevenueOne.synthetic)} subtitle="Synthetic control" icon={Activity} accent="blue" />
                <MetricCard title="Actual Sales" value={formatNumber(selectedSalesOne.actual)} subtitle={formatDate(interventionDate)} icon={ChartNoAxesCombined} accent="orange" />
                <MetricCard title="Synthetic Sales" value={formatNumber(selectedSalesOne.synthetic)} subtitle="Synthetic control" icon={Database} accent="green" />
              </section>
              <h4>Revenue record</h4>
              <DataTable rows={selectedRevenue} emptyText="No revenue record for this date." />
              <h4>Sales record</h4>
              <DataTable rows={selectedSales} emptyText="No sales record for this date." />
            </ChartCard>

            <section className="lower-grid">
              <ChartCard title="Donor Region Weights" subtitle="Actual synthetic-control weights from model output">
                {donorData.length ? <ResponsiveContainer width="100%" height={310}>
                  <BarChart data={donorData} layout="vertical" margin={{ top: 4, right: 18, left: 10, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#edf0f5" />
                    <XAxis type="number" tickFormatter={(v) => `${v.toFixed(0)}%`} tickLine={false} axisLine={false} tick={{ fill: "#8791a5", fontSize: 11 }} />
                    <YAxis type="category" dataKey="region" width={88} tickLine={false} axisLine={false} tick={{ fill: "#657087", fontSize: 11 }} />
                    <Tooltip formatter={(v) => `${formatNumber(v)}%`} />
                    <Bar dataKey="weight" name="Weight" fill="#6974ec" radius={[0, 5, 5, 0]} barSize={17} />
                  </BarChart>
                </ResponsiveContainer> : <div className="empty-state">{loading ? "Loading weights…" : "No donor weights returned. Check /api/weights."}</div>}
              </ChartCard>
              <ChartCard title="Model Summary" subtitle="Metrics returned by synthetic_control_summary.csv">
                {summaryRows.length ? <DataTable rows={summaryRows} /> : <div className="empty-state">{loading ? "Loading model summary…" : "No summary rows returned. Check /api/summary."}</div>}
              </ChartCard>
            </section>
          </>}

          {activePage === "Revenue Analysis" && (
            <OutcomeAnalysis
              rows={revenueRows}
              label="Revenue"
              subtitle="Revenue_Proxy_synthetic_control.csv"
              selectedDate={revenueDate}
              availableDates={["", ...[...new Set(revenueRows.map((r) => r.date))].sort().filter(Boolean)]}
              onDateChange={setRevenueDate}
            />
          )}
          {activePage === "Sales Analysis" && (
            <OutcomeAnalysis
              rows={salesRows}
              label="Sales"
              subtitle="Sales_Volume_synthetic_control.csv"
              selectedDate={salesDate}
              availableDates={["", ...[...new Set(salesRows.map((r) => r.date))].sort().filter(Boolean)]}
              onDateChange={setSalesDate}
            />
          )}

          {activePage === "Causal Impact" && <>
            <section className="metrics-grid">
              <MetricCard title="Average Post-Treatment Gap" value={avgGap === null ? "—" : formatNumber(avgGap)} subtitle="From summary CSV" icon={GitCompareArrows} accent="purple" />
              <MetricCard title="Summary Outcomes" value={String(summaryRows.length).padStart(2, "0")} subtitle="Rows returned by the model summary" icon={Activity} accent="blue" />
            </section>
            <ChartCard title="Causal Impact Summary" subtitle="Pre-treatment fit and post-treatment gaps from the Python analysis">
              <DataTable rows={summaryRows} emptyText="No summary output loaded. Check synthetic_control_summary.csv and /api/summary." />
            </ChartCard>
          </>}

          {activePage === "Placebo Tests" && <ChartCard title="Placebo Test Results" subtitle="Rows returned by placebo_test_results.csv">
            <DataTable rows={placeboRows} emptyText="No placebo results returned. Confirm placebo_test_results.csv exists and /api/placebo returns it." />
          </ChartCard>}

          {activePage === "Data Explorer" && <ChartCard title="Analysis-Ready Dataset" subtitle="Rows returned by analysis_ready_data.csv">
            <DataTable rows={sourceRows.slice(0, 250)} emptyText="No analysis-ready data returned. Check /api/data." />
            {sourceRows.length > 250 && <p className="table-footnote">Showing first 250 of {sourceRows.length.toLocaleString()} rows for browser performance.</p>}
          </ChartCard>}

          <footer className="footer">
            <span>SynthControl · Causal Analytics</span>
            <span>{apiOnline ? "Live Python API results" : "Waiting for backend connection"}</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
