import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="logo">HiveLogic</div>

      <div className="nav-links">
        <NavLink to="/"          end>Dashboard</NavLink>
        <NavLink to="/reports"      >Reports</NavLink>
        <NavLink to="/watchlist"    >Watchlist</NavLink>
        <NavLink to="/graph"        >GraphRAG</NavLink>
      </div>
    </nav>
  );
}