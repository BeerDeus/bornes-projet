// Config centralisée - cf. Roadmap Phase 2. En dev local, surchargeable via
// un fichier .env (voir .env.example) ; par défaut pointe sur le backend
// déployé en continu sur Hostinger (cf. bornes-projet/README.md).
export const SERVEUR_URL = import.meta.env.VITE_SERVEUR_URL || "https://bowling.m2s-photo.fr";
export const API_URL = `${SERVEUR_URL}/api`;
