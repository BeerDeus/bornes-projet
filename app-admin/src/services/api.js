// Client REST vers le Back-Office backend (routes /api/admin/*, cf.
// backend/src/routes/adminCommandes.js).
import { API_URL } from "../config";
import { obtenirToken, viderSession } from "./sessionStorage";

// Exporté (pas juste utilisé en interne) : services/auth.js le réutilise
// pour /api/auth/login et /api/auth/moi plutôt que de dupliquer la logique
// fetch/gestion d'erreur ici.
export async function requeteJson(chemin, options) {
  const token = obtenirToken();
  const reponse = await fetch(`${API_URL}${chemin}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });

  // 401 = token absent/invalide/expiré (cf. backend/src/middlewareAuth.js) -
  // la session locale ne veut plus rien dire, on la vide immédiatement :
  // sans ça, l'app resterait dans un état "connecté" en apparence
  // (utilisateur toujours en mémoire) alors que chaque appel API échoue.
  if (reponse.status === 401) {
    viderSession();
  }

  const corps = await reponse.json().catch(() => null);
  if (!reponse.ok) {
    const erreur = new Error((corps && corps.erreur) || `Erreur HTTP ${reponse.status}`);
    erreur.statut = reponse.status;
    erreur.corps = corps;
    throw erreur;
  }
  return corps;
}

export const api = {
  // { module, statut, page, pageSize } - tous optionnels.
  getCommandes: (params = {}) => {
    const query = new URLSearchParams();
    for (const [cle, valeur] of Object.entries(params)) {
      if (valeur !== undefined && valeur !== null && valeur !== "") query.set(cle, valeur);
    }
    const suffixe = query.toString() ? `?${query.toString()}` : "";
    return requeteJson(`/admin/commandes${suffixe}`);
  },
  getCommande: (id) => requeteJson(`/admin/commandes/${id}`),
  getStatut: () => requeteJson("/admin/statut"),

  // Paramètres Bowling - tarification par plage horaire (cf.
  // backend/src/routes/adminTarifsBowling.js). Pas encore branché sur le
  // calcul réel d'un prix de commande (cf. commentaire dans ce routeur) -
  // uniquement de la configuration pour l'instant.
  getTarifsBowling: () => requeteJson("/admin/bowling/tarifs"),
  creerTarifBowling: (payload) =>
    requeteJson("/admin/bowling/tarifs", { method: "POST", body: JSON.stringify(payload) }),
  modifierTarifBowling: (id, payload) =>
    requeteJson(`/admin/bowling/tarifs/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  supprimerTarifBowling: (id) => requeteJson(`/admin/bowling/tarifs/${id}`, { method: "DELETE" }),
};
