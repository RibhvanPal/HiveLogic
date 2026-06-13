import { useState, useEffect } from "react";
import API from "../services/api";

export default function Watchlist() {
  const [ticker, setTicker] = useState("");
  const [items, setItems]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding]   = useState(false);
  const [removing, setRemoving] = useState(null);

  useEffect(() => { load(); }, []);

  const load = async () => {
    setLoading(true);
    try {
      const res = await API.get("/watchlist");
      const raw = res.data ?? [];
      const normalised = raw.map((item) => ({
        ...item,
        ticker: item.ticker ?? item.symbol ?? item.name ?? null,
      })).filter((item) => item.ticker && item.ticker.trim() !== ""); 
      setItems(normalised);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const add = async () => {
    if (!ticker.trim()) return;
    setAdding(true);
    try {
      await API.post("/watchlist", { ticker: ticker.trim().toUpperCase() });
      setTicker("");
      await load();
    } catch (err) {
      console.error(err);
    } finally {
      setAdding(false);
    }
  };

  const remove = async (item) => {
    const key = item.ticker?.trim() || null;
    setRemoving(key ?? item.id);
    try {
      const url = key ? `/watchlist/${key}` : `/watchlist/${item.id}`;
      await API.delete(url);
      setItems((prev) => prev.filter((i) => i.id !== item.id));
    } catch (err) {
      console.error(err);
    } finally {
      setRemoving(null);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") add();
  };

  return (
    <div className="container">

      <div className="page-header">
        <h1 className="page-title">Watchlist</h1>
        <p className="page-subtitle">
          {items.length > 0
            ? `Tracking ${items.length} ticker${items.length !== 1 ? "s" : ""}`
            : "No tickers added yet"}
        </p>
      </div>

      <div className="watchlist-add-row">
        <input
          className="watchlist-input"
          placeholder="Add ticker - e.g. AAPL or RELIANCE.NS"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          onKeyDown={handleKeyDown}
        />
        <button
          className="btn btn-primary"
          onClick={add}
          disabled={adding || !ticker.trim()}
        >
          {adding ? "Adding…" : "Add"}
        </button>
      </div>

      {loading && <div className="loading-bar" style={{ marginTop: 24 }} />}

      {!loading && items.length === 0 && (
        <div className="reports-empty">
          <span className="reports-empty-icon">-</span>
          <p>No tickers yet. Add one above to start tracking.</p>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="reports-table-wrap" style={{ marginTop: 24 }}>
          <table className="reports-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Ticker</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => (
                <tr key={item.id}>
                  <td className="watchlist-index">{String(idx + 1).padStart(2, "0")}</td>
                  <td className="reports-ticker">{item.ticker}</td>
                  <td className="reports-actions">
                    <button
                      className="btn-delete"
                      onClick={() => remove(item)}
                      disabled={removing === (item.ticker || item.id)}
                    >
                      {removing === (item.ticker || item.id) ? "…" : "Remove"}
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