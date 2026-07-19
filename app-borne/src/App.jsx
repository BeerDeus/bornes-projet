import { Route, Routes } from "react-router-dom";
import ConnectionWatcher from "./components/ConnectionWatcher";
import BanniereDegradee from "./components/BanniereDegradee";
import Accueil from "./pages/Accueil";
import Bar from "./pages/Bar";
import Bowling from "./pages/Bowling";

export default function App() {
  return (
    <div style={{ fontFamily: "sans-serif" }}>
      <ConnectionWatcher />
      <BanniereDegradee />
      <Routes>
        <Route path="/" element={<Accueil />} />
        <Route path="/bar" element={<Bar />} />
        <Route path="/bowling" element={<Bowling />} />
      </Routes>
    </div>
  );
}
