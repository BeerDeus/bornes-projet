// Config centralisée - cf. Roadmap Phase 2. Surchargeable via un fichier
// .env.local (voir .env.example) ; par défaut pointe sur le backend local
// (port 3000) de la machine qui sert la page : marche sur le PC backend comme
// depuis une tablette du même Wi-Fi qui ouvre l'IP du PC (cf. README racine).
export const SERVEUR_URL = import.meta.env.VITE_SERVEUR_URL || `http://${window.location.hostname}:3000`;
export const API_URL = `${SERVEUR_URL}/api`;
