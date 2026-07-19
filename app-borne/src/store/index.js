import { configureStore } from "@reduxjs/toolkit";
import panierReducer from "./cartSlice";
import catalogueReducer from "./catalogSlice";
import connexionReducer from "./connectionSlice";

export const store = configureStore({
  reducer: {
    panier: panierReducer,
    catalogue: catalogueReducer,
    connexion: connexionReducer,
  },
});
