import { BrowserRouter, Routes, Route } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Reports from "./pages/Reports";
import Watchlist from "./pages/Watchlist";
import Graph from "./pages/Graph";
import Chat from "./pages/Chat";

import Navbar from "./components/Navbar";

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/graph" element={<Graph />} />

        <Route
          path="/chat/:reportId"
          element={<Chat />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;