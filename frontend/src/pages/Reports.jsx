import { useEffect, useState } from "react";
import API from "../services/api";
import { useNavigate } from "react-router-dom";

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(null);
  const navigate = useNavigate();

  useEffect(() => { loadReports(); }, []);

  const loadReports = async () => {
    setLoading(true);
    try {
      const res = await API.get("/reports");
      setReports(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const deleteReport = async (id) => {
    setDeleting(id);
    try {
      await API.delete(`/reports/${id}`);
      setReports((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(null);
    }
  };

  const sentimentClass = (label) => {
    const l = label?.toLowerCase();
    if (l === "bullish") return "badge badge-bullish";
    if (l === "bearish") return "badge badge-bearish";
    return "badge badge-neutral";
  };

  return (
    <div className="container">

      <div className="page-header">
        <h1 className="page-title">Reports</h1>
        <p className="page-subtitle">
          {reports.length > 0
            ? `${reports.length} saved report${reports.length !== 1 ? "s" : ""}`
            : "No reports yet"}
        </p>
      </div>

      {loading && <div className="loading-bar" />}

      {!loading && reports.length === 0 && (
        <div className="reports-empty">
          <span className="reports-empty-icon">-</span>
          <p>No reports saved yet. Run an analysis from the Dashboard.</p>
        </div>
      )}

      {!loading && reports.length > 0 && (
        <div className="reports-table-wrap">
          <table className="reports-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Query</th>
                <th>Sentiment</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r.report_id}>
                  <td className="reports-ticker">{r.ticker}</td>
                  <td className="reports-query">{r.query}</td>
                  <td>
                    <span className={sentimentClass(r.sentiment_label)}>
                      {r.sentiment_label ?? "-"}
                    </span>
                  </td>
                  <td className="reports-actions">

                    <button
                      className="btn-chat"
                      onClick={() =>
                        navigate(`/chat/${r.report_id}`)
                      }
                    >
                      Chat
                    </button>

                    <button
                      className="btn-delete"
                      onClick={() =>
                        deleteReport(r.report_id)
                      }
                      disabled={
                        deleting === r.report_id
                      }
                    >
                      {deleting === r.report_id
                        ? "…"
                        : "Delete"}
                    </button>

                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}