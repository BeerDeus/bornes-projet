import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import CommandesListe from "./pages/CommandesListe";
import CommandeDetail from "./pages/CommandeDetail";
import ModuleParametres from "./pages/ModuleParametres";
import StatutSysteme from "./pages/StatutSysteme";

export default function App() {
  return (
    <Layout>
      <Routes>
        {/* Bowling en page d'accueil par défaut (module le plus avancé à ce jour). */}
        <Route path="/" element={<Navigate to="/bowling/commandes" replace />} />
        <Route path="/statut" element={<StatutSysteme />} />
        <Route path="/:module/commandes" element={<CommandesListe />} />
        <Route path="/:module/commandes/:id" element={<CommandeDetail />} />
        <Route path="/:module/parametres" element={<ModuleParametres />} />
        <Route path="*" element={<Navigate to="/bowling/commandes" replace />} />
      </Routes>
    </Layout>
  );
}
