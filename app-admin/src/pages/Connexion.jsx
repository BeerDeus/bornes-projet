// Page de connexion Back-Office (cf. demande Beer 2026-07-21 - sécuriser
// /api/admin/*). Identifiants créés via backend/prisma/seed.js (pas
// d'inscription en self-service, cf. backend/src/routes/auth.js).
import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexteAuth";

export default function Connexion() {
  const { utilisateur, connecter } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState(null);
  const [soumission, setSoumission] = useState(false);

  // Déjà connecté (ex: onglet ouvert avant expiration, ou retour arrière
  // après login) -> renvoie directement vers la page visée initialement.
  if (utilisateur) {
    return <Navigate to={location.state?.depuis?.pathname || "/"} replace />;
  }

  async function soumettre(e) {
    e.preventDefault();
    setErreur(null);
    setSoumission(true);
    try {
      await connecter(email.trim(), motDePasse);
      navigate(location.state?.depuis?.pathname || "/bowling/commandes", { replace: true });
    } catch (exc) {
      setErreur(exc.statut === 401 ? "Email ou mot de passe incorrect." : exc.message);
    } finally {
      setSoumission(false);
    }
  }

  return (
    <div className="page-connexion">
      <form className="carte carte-connexion" onSubmit={soumettre}>
        <div className="connexion-entete">
          <span className="sidebar-logo">BB</span>
          <div className="sidebar-titre-texte">
            Back-Office
            <small>Bornes Bowling</small>
          </div>
        </div>

        <div className="champ-formulaire">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div className="champ-formulaire">
          <label htmlFor="motDePasse">Mot de passe</label>
          <input
            id="motDePasse"
            type="password"
            autoComplete="current-password"
            value={motDePasse}
            onChange={(e) => setMotDePasse(e.target.value)}
            required
          />
        </div>

        {erreur && <p className="texte-erreur-formulaire">{erreur}</p>}

        <button type="submit" className="bouton-primaire bouton-connexion" disabled={soumission}>
          {soumission ? "Connexion…" : "Se connecter"}
        </button>
      </form>
    </div>
  );
}
