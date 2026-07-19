// Client REST vers le backend (catalogue + commandes bar) - cf. Roadmap Phase 2.
// Pas de logique métier ici (calcul du total, validations) : tout est
// recalculé/validé côté serveur (cf. backend/src/routes/commandes.js), ce
// client se contente de relayer les appels.
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
  getCategories: () => requeteJson("/categories"),
  getProduits: () => requeteJson("/produits"),
  creerCommande: (payload) =>
    requeteJson("/commandes", { method: "POST", body: JSON.stringify(payload) }),
  getCommande: (id) => requeteJson(`/commandes/${id}`),
  patchStatutCommande: (id, payload) =>
    requeteJson(`/commandes/${id}/statut`, { method: "PATCH", body: JSON.stringify(payload) }),
  creerCommandeBowling: (payload) =>
    requeteJson("/commandes-bowling", { method: "POST", body: JSON.stringify(payload) }),
};
