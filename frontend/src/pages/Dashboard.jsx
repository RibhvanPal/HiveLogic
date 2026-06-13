import { useState } from "react";
import API from "../services/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function Dashboard() {
  const [ticker, setTicker]   = useState("");
  const [query,  setQuery]    = useState("");
  const [pdf,    setPdf]      = useState(null);
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("ticker", ticker);
      formData.append("query",  query);
      if (pdf) formData.append("pdf_file", pdf);

      const response = await API.post("/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(response.data);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    const blob = new Blob([result.report], { type: "text/markdown" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `${ticker}.md`;
    a.click();
  };

  const sentimentClass = (label) => {
    const l = label?.toLowerCase();
    if (l === "bullish") return "badge badge-bullish";
    if (l === "bearish") return "badge badge-bearish";
    return "badge badge-neutral";
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
        <h1 className="page-title">Financial Analysis</h1>
        <p className="page-subtitle">
          Enter a ticker and research query to generate a multi-agent report.
        </p>
      </div>

      <div className="input-group">
        <input
          placeholder="Ticker symbol - e.g. RELIANCE.NS"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
        />
        <textarea
          placeholder="Research query - e.g. Analyse Q4 earnings and debt levels"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <label className="file-label">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          {pdf
            ? <span className="file-name">{pdf.name}</span>
            : <span>Attach annual report PDF - optional</span>
          }
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setPdf(e.target.files[0])}
          />
        </label>
      </div>

      <button
        className="btn btn-primary"
        onClick={analyze}
        disabled={loading || !ticker || !query}
      >
        {loading ? "Analysing…" : "Run Analysis"}
      </button>

      {loading && <div className="loading-bar" style={{ marginTop: 24 }} />}

      {result && !loading && (
        <>
          <hr className="divider" />

          <div className="result-header">
            <div>
              <div className="result-ticker">{result.ticker}</div>
              <div className="badge-row">
                <span className={sentimentClass(result.sentiment?.label)}>
                  {result.sentiment?.label ?? "-"}
                </span>
                <span className="badge badge-verified">
                  {result.verified ? "Verified" : "Needs Review"}
                </span>
              </div>
            </div>
            <button className="btn btn-ghost" onClick={downloadReport}>
              Download .md
            </button>
          </div>

          <p className="section-label">Key Metrics</p>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-title">Current Price</div>
              <div className="metric-value">
                ${result.financial_metrics?.current_price ?? "-"}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-title">Market Cap</div>
              <div className="metric-value">
                {result.financial_metrics?.market_cap_fmt ?? "-"}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-title">P/E Ratio</div>
              <div className="metric-value">
                {result.financial_metrics?.pe_ratio?.toFixed(2) ?? "-"}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-title">EPS</div>
              <div className="metric-value">
                {result.financial_metrics?.eps ?? "-"}
              </div>
            </div>
          </div>

          <p className="section-label">Research Report</p>
          <div className="panel" style={{ marginBottom: 36 }}>
            <div className="report-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.report}</ReactMarkdown>
            </div>
          </div>

          {result.citations?.length > 0 && (
            <>
              <p className="section-label">Sources</p>
              <div className="citation-list" style={{ marginBottom: 36 }}>
                {result.citations.map((c, i) => (
                  <div key={i} className="citation-card">
                    <div className="citation-claim">{c.claim}</div>
                    <div className="citation-source">{c.source}</div>
                    {c.url && (
                      <a href={c.url} target="_blank" rel="noreferrer"
                         className="citation-link">
                        Open source ↗
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}

          {result.contagion_risks?.length > 0 && (
            <>
              <p className="section-label">Contagion Risks</p>
              <table className="risk-table" style={{ marginBottom: 36 }}>
                  <thead>
                    <tr>
                      <th>Entity</th>
                      <th>Relation</th>
                      <th>Risk</th>
                      <th>Severity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.contagion_risks.map((risk, i) => (
                      <tr key={i}>
                        <td>{risk.entity}</td>
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
            </>
          )}

          {result.verification_notes && (
            <>
              <p className="section-label">Verification Notes</p>
              <div className="panel">
                <pre className="verification-notes">
                  {result.verification_notes}
                </pre>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}