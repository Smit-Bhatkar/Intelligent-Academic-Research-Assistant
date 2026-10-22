import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Search from "./pages/Search";
import Assistant from "./pages/Assistant";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="border-b border-gray-200 px-6 py-4 flex gap-6 items-center bg-white shadow-2xs">
        <Link to="/" className="font-bold text-navy text-lg tracking-tight">
          ARA
        </Link>
        <Link to="/search" className="text-sm text-gray-600 hover:text-navy transition-colors">
          Search Papers
        </Link>
        <Link
          to="/assistant"
          className="text-sm font-medium text-navy hover:text-accent transition-colors"
        >
          Research Assistant
        </Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/assistant" element={<Assistant />} />
      </Routes>
    </BrowserRouter>
  );
}
