// Client REST vers le Back-Office backend (routes /api/admin/*, cf.
// backend/src/routes/adminCommandes.js) - lecture seule.
import { API_URL } from "../config";

async function requeteJson(chemin, options) {
  const reponse = await fetch(`${API_URL}${chemin}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
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
};
