import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Search from "./pages/Search";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="border-b border-gray-200 px-6 py-4 flex gap-6 items-center">
        <Link to="/" className="font-bold text-navy">
          ARA
        </Link>
        <Link to="/search" className="text-gray-600 hover:text-navy">
          Search
        </Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
      </Routes>
    </BrowserRouter>
  );
}
