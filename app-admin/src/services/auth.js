// Auth Back-Office (cf. backend/src/routes/auth.js) - login + vérification
// de session. Réutilise requeteJson (services/api.js) plutôt que de
// dupliquer la logique fetch/gestion d'erreur.
import { requeteJson } from "./api";
import { definirSession, obtenirToken, obtenirUtilisateur, viderSession } from "./sessionStorage";

export async function connexion(email, motDePasse) {
  const { token, utilisateur } = await requeteJson("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, motDePasse }),
  });
  definirSession(token, utilisateur);
  return utilisateur;
}

export function deconnexion() {
  viderSession();
}

// Vérifie auprès du serveur que le token stocké est toujours valide (pas
// expiré, compte toujours actif) - sans ça, un token expiré depuis la
// dernière visite laisserait croire l'utilisateur "connecté" jusqu'au
// premier appel /api/admin/* qui échouerait en 401 (cf. requeteJson).
// Renvoie l'utilisateur si la session tient, null sinon (et vide la session
// locale dans ce cas).
export async function verifierSession() {
  if (!obtenirToken()) return null;
  try {
    const { utilisateur } = await requeteJson("/auth/moi");
    return utilisateur;
  } catch (_exc) {
    viderSession();
    return null;
  }
}

export { obtenirUtilisateur };
