// Stockage de la session Back-Office (token JWT + utilisateur courant) - cf.
// demande Beer 2026-07-21 (sécuriser /api/admin/*). En localStorage, même
// pattern que le thème (cf. hooks/useTheme.js) : survit à un rechargement de
// page, ce qu'un simple state React ne ferait pas. Le serveur reste la seule
// source de vérité sur la validité du token (expiration, révocation) -
// cf. verifierSession() dans auth.js, appelée au chargement de l'app.
const CLE_TOKEN = "admin_session_token";
const CLE_UTILISATEUR = "admin_session_utilisateur";

export function obtenirToken() {
  try {
    return localStorage.getItem(CLE_TOKEN);
  } catch (_exc) {
    return null;
  }
}

export function obtenirUtilisateur() {
  try {
    const brut = localStorage.getItem(CLE_UTILISATEUR);
    return brut ? JSON.parse(brut) : null;
  } catch (_exc) {
    return null;
  }
}

export function definirSession(token, utilisateur) {
  try {
    localStorage.setItem(CLE_TOKEN, token);
    localStorage.setItem(CLE_UTILISATEUR, JSON.stringify(utilisateur));
  } catch (_exc) {
    // localStorage indisponible - la session reste active en mémoire pour la
    // page en cours (le contexte React garde l'utilisateur), juste non
    // persistante entre rechargements.
  }
}

// Nom de l'événement DOM émis à chaque vidage de session (cf. api.js sur un
// 401 en cours de navigation) - permet au contexte React (contexteAuth.jsx)
// de se resynchroniser immédiatement sans attendre un rechargement de page,
// sinon l'UI resterait "connectée en apparence" pendant que chaque appel API
// échoue silencieusement en arrière-plan.
export const EVENEMENT_SESSION_EXPIREE = "admin-session-expiree";

export function viderSession() {
  try {
    localStorage.removeItem(CLE_TOKEN);
    localStorage.removeItem(CLE_UTILISATEUR);
  } catch (_exc) {
    /* rien à faire */
  } finally {
    window.dispatchEvent(new Event(EVENEMENT_SESSION_EXPIREE));
  }
}
