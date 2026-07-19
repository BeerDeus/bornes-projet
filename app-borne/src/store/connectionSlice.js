// État de connexion temps réel - alimente le mode dégradé (CDC 2.1) : la
// borne doit détecter la perte de connexion au backend (heartbeat WebSocket)
// et basculer sur un écran "Service momentanément indisponible" plutôt que
// de laisser composer une commande qui ne pourra jamais aboutir.
import { createSlice } from "@reduxjs/toolkit";

const connectionSlice = createSlice({
  name: "connexion",
  initialState: {
    socketConnecte: false,
    botConnecte: false,
  },
  reducers: {
    setSocketConnecte(state, action) {
      state.socketConnecte = action.payload;
    },
    setBotConnecte(state, action) {
      state.botConnecte = action.payload;
    },
  },
});

export const { setSocketConnecte, setBotConnecte } = connectionSlice.actions;
// Aucune commande financière ne doit être acceptée si le backend est
// injoignable (cf. CDC 2.1) - le statut du bot, lui, n'empêche que le module
// Bowling (le Bar peut fonctionner même bot déconnecté).
export const selectionnerServiceIndisponible = (state) => !state.connexion.socketConnecte;
export default connectionSlice.reducer;
