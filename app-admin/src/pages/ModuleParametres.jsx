// Paramètres par module, cf. demande Beer 2026-07-19. Bowling a désormais un
// vrai écran (tarification par plage horaire, cf.
// components/ParametresBowlingTarifs.jsx) - les autres modules (Bar,
// Karaoké, Quiz) n'ont encore aucun paramètre concret défini côté CDC/
// backend : ils gardent le placeholder, à remplacer au fur et à mesure que
// les besoins seront précisés module par module.
import { Navigate, useParams } from "react-router-dom";
import { moduleParCle } from "../config";
import ParametresBowlingTarifs from "../components/ParametresBowlingTarifs";

export default function ModuleParametres() {
  const { module: moduleCle } = useParams();
  const module = moduleParCle(moduleCle);

  if (!module) return <Navigate to="/bowling/commandes" replace />;

  return (
    <>
      <div className="fil-ariane">{module.label}</div>
      <div className="entete-page">
        <h1>Paramètres — {module.label}</h1>
      </div>

      {module.cle === "bowling" ? (
        <ParametresBowlingTarifs />
      ) : (
        <div className="encart-placeholder">Aucun paramètre configurable pour l'instant. À venir.</div>
      )}
    </>
  );
}
