// Garde de route Back-Office - redirige vers /connexion si pas de session
// valide (cf. contexteAuth.jsx). La vraie autorisation reste appliquée
// côté serveur (exigerAuth/exigerRole, cf. backend/src/middlewareAuth.js) -
// ce garde est une commodité UX (éviter d'afficher un écran plein d'erreurs
// 401), pas la protection elle-même.
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexteAuth";

export default function RequireAuth({ children }) {
  const { utilisateur, verificationEnCours } = useAuth();
  const location = useLocation();

  if (verificationEnCours) {
    return <div className="etat-chargement">Vérification de la session…</div>;
  }

  if (!utilisateur) {
    return <Navigate to="/connexion" state={{ depuis: location }} replace />;
  }

  return children;
}
