import { useState } from "react";
import API from "../services/api";
import GraphViewer from "../components/GraphViewer";
export default function Graph() {
  const [ticker, setTicker]       = useState("");
  const [risks, setRisks]         = useState([]);
  const [stats, setStats]         = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingRisks, setLoadingRisks] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const loadStats = async () => {
    setLoadingStats(true);
    try {
      const res = await API.get("/graph/stats");
      setStats(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingStats(false);
    }
  };

  const loadRisks = async () => {
    if (!ticker.trim()) return;

    setLoadingRisks(true);
    setGraphData(null);
    setRisks([]);
    try {
      const res = await API.get(
        `/graph/risks/${ticker.trim()}`
      );

      setRisks(res.data.risks ?? []);

      const graphRes = await API.get(
        `/graph/subgraph/${ticker.trim()}`
      );

      setGraphData(graphRes.data);

    } catch (err) {
      console.error(err);
    } finally {
      setLoadingRisks(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") loadRisks();
  };

  const severityClass = (s) => {
    const l = s?.toLowerCase();
    if (l === "high")   return "severity-high";
    if (l === "medium") return "severity-medium";
    return "severity-low";
  };

  return (
    <div className="container">

      <div className="page-header">
        <h1 className="page-title">GraphRAG</h1>
        <p className="page-subtitle">
          Explore knowledge graph structure and contagion risk chains.
        </p>
      </div>

      <p className="section-label">Graph Stats</p>

      <div className="graph-stats-row">
        {stats ? (
        Object.entries(stats).map(([key, val]) => {
            const isLongList = typeof val === "string" && val.includes(",") && val.split(",").length > 3;
            const isList     = Array.isArray(val);
            const items      = isList ? val : isLongList ? val.split(",").map(s => s.trim()) : null;

            return (
              <div key={key} className="metric-card">
                <div className="metric-title">
                  {key.replace(/_/g, " ")}
                </div>
                {items ? (
                  <div className="graph-tag-list">
                    {items.map((item, i) => (
                      <span key={i} className="graph-tag">{item}</span>
                    ))}
                  </div>
                ) : (
                  <div className="metric-value">
                    {typeof val === "number" ? val.toLocaleString() : String(val)}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="graph-stats-empty">
            <p>Load the graph to see node and edge counts.</p>
            <button
              className="btn btn-ghost"
              onClick={loadStats}
              disabled={loadingStats}
            >
              {loadingStats ? "Loading…" : "Load Stats"}
            </button>
          </div>
        )}
      </div>

      {stats && (
        <button
          className="btn btn-ghost"
          onClick={loadStats}
          disabled={loadingStats}
          style={{ marginTop: 14 }}
        >
          {loadingStats ? "Refreshing…" : "Refresh"}
        </button>
      )}

      <p className="section-label">Contagion Risk Lookup</p>

      <div className="watchlist-add-row" style={{ marginBottom: 24 }}>
        <input
          className="watchlist-input"
          placeholder="Ticker - e.g. AAPL or RELIANCE.NS"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          onKeyDown={handleKeyDown}
        />
        <button
          className="btn btn-primary"
          onClick={loadRisks}
          disabled={loadingRisks || !ticker.trim()}
        >
          {loadingRisks ? "Fetching…" : "Get Risks"}
        </button>
      </div>

      {loadingRisks && <div className="loading-bar" />}

      {!loadingRisks && risks.length === 0 && ticker && (
        <div className="reports-empty">
          <span className="reports-empty-icon">-</span>
          <p>No contagion risks found for <span style={{ fontFamily: "var(--mono)", color: "var(--text-secondary)" }}>{ticker}</span>.</p>
        </div>
      )}
      
      {!loadingRisks && risks.length > 0 && (
        <div className="reports-table-wrap">
          <table className="risk-table">
            <thead>
              <tr>
                <th>Entity</th>
                <th>Relation</th>
                <th>Risk</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {risks.map((risk, i) => (
                <tr key={i}>
                  <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                    {risk.entity}
                  </td>
                  <td>{risk.relation}</td>
                  <td>{(risk.risk_weight * 100).toFixed(0)}%</td>
                  <td>
                    <span className={`severity-pill ${severityClass(risk.severity)}`}>
                      {risk.severity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {graphData && (
        <>
          <p
            className="section-label"
            style={{ marginTop: 30 }}
          >
            Relationship Graph
          </p>

          <GraphViewer
            nodes={graphData.nodes}
            edges={graphData.edges}
          />
        </>
      )}

    </div>
  );
}