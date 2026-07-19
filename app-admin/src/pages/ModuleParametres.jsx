// Placeholder - paramètres par module, cf. demande Beer 2026-07-19 ("les
// paramètres des modules qu'on mettra plus tard"). Aucun paramètre concret
// n'est encore défini côté CDC/backend (pas de modèle de config en base) :
// cet écran sert juste à réserver la place dans le menu, à remplir dès que
// les besoins seront précisés module par module.
import { Navigate, useParams } from "react-router-dom";
import { moduleParCle } from "../config";

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
      <div className="encart-placeholder">Aucun paramètre configurable pour l'instant. À venir.</div>
    </>
  );
}
