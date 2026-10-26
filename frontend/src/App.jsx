import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Auth from "./pages/Auth";
import Home from "./pages/Home";
import Products from "./pages/Products";
import Routine from "./pages/Routine";
import Tips from "./pages/Tips";
import Profile from "./pages/Profile";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Auth />} />
        <Route path="/home" element={<Home />} />
        <Route path="/products" element={<Products />} />
        <Route path="/routine" element={<Routine />} />
        <Route path="/tips" element={<Tips />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;