// Panier Bar - persistant en localStorage pour survivre à une coupure réseau
// courte ou un rechargement de page (cf. CDC 2.1 - "panier persistant en cas
// de coupure réseau courte"). Aucune commande n'est envoyée au serveur tant
// que l'utilisateur n'a pas validé explicitement (cf. Bar.jsx) : le panier
// local n'est qu'un brouillon, jamais une transaction financière en soi.
import { createSlice } from "@reduxjs/toolkit";

const CLE_STOCKAGE = "borne_panier_v1";

function chargerPanierInitial() {
  try {
    const brut = window.localStorage.getItem(CLE_STOCKAGE);
    return brut ? JSON.parse(brut) : [];
  } catch (_exc) {
    return []; // localStorage indisponible ou corrompu -> panier vide, pas de crash
  }
}

function sauvegarder(lignes) {
  try {
    window.localStorage.setItem(CLE_STOCKAGE, JSON.stringify(lignes));
  } catch (_exc) {
    // best-effort : si le stockage est plein/indisponible, le panier reste
    // fonctionnel en mémoire pour la session en cours, juste non persistant.
  }
}

const cartSlice = createSlice({
  name: "panier",
  initialState: { lignes: chargerPanierInitial() },
  reducers: {
    ajouterProduit(state, action) {
      const produit = action.payload;
      const existante = state.lignes.find((l) => l.produitId === produit.id);
      if (existante) {
        existante.quantite += 1;
      } else {
        state.lignes.push({
          produitId: produit.id,
          nom: produit.nom,
          prixCentimes: produit.prixCentimes,
          quantite: 1,
        });
      }
      sauvegarder(state.lignes);
    },
    retirerProduit(state, action) {
      const produitId = action.payload;
      const existante = state.lignes.find((l) => l.produitId === produitId);
      if (existante) {
        existante.quantite -= 1;
        if (existante.quantite <= 0) {
          state.lignes = state.lignes.filter((l) => l.produitId !== produitId);
        }
      }
      sauvegarder(state.lignes);
    },
    viderPanier(state) {
      state.lignes = [];
      sauvegarder(state.lignes);
    },
  },
});

export const { ajouterProduit, retirerProduit, viderPanier } = cartSlice.actions;
export const selectionnerTotalCentimes = (state) =>
  state.panier.lignes.reduce((total, l) => total + l.prixCentimes * l.quantite, 0);
export default cartSlice.reducer;
