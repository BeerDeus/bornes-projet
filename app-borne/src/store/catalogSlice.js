// Catalogue Bar - récupéré depuis le backend (BDD PostgreSQL, cf. Phase 2).
import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { api } from "../services/api";

export const chargerCatalogue = createAsyncThunk("catalogue/charger", async () => {
  const [categories, produits] = await Promise.all([api.getCategories(), api.getProduits()]);
  return { categories, produits };
});

const catalogSlice = createSlice({
  name: "catalogue",
  initialState: { categories: [], produits: [], statut: "inactif", erreur: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(chargerCatalogue.pending, (state) => {
        state.statut = "chargement";
        state.erreur = null;
      })
      .addCase(chargerCatalogue.fulfilled, (state, action) => {
        state.statut = "pret";
        state.categories = action.payload.categories;
        state.produits = action.payload.produits;
      })
      .addCase(chargerCatalogue.rejected, (state, action) => {
        state.statut = "erreur";
        state.erreur = action.error.message;
      });
  },
});

export default catalogSlice.reducer;
