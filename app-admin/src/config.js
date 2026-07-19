// Config centralisée - même approche que app-borne/src/config.js. En dev
// local, surchargeable via un fichier .env.local (voir .env.example) ; par
// défaut pointe sur le backend déployé en continu sur Hostinger.
export const SERVEUR_URL = import.meta.env.VITE_SERVEUR_URL || "https://bowling.m2s-photo.fr";
export const API_URL = `${SERVEUR_URL}/api`;

// Modules gérés par le Back-Office (cf. enum ModuleCommande en base et
// backend/src/numeroCommande.js pour les préfixes BOxxx/BAxxx/KAxxx/QZxxx).
// KARAOKE et QUIZ n'ont pas encore de parcours borne développé (aucune
// commande ne peut encore être créée pour ces modules) - ils apparaissent
// quand même dans le menu, prêts à l'emploi dès que le module sera codé,
// plutôt que de les ajouter en dur plus tard dans le menu ET dans la BDD.
export const MODULES = [
  { cle: "bowling", label: "Bowling", moduleDb: "BOWLING" },
  { cle: "bar", label: "Bar", moduleDb: "BAR" },
  { cle: "karaoke", label: "Karaoké", moduleDb: "KARAOKE" },
  { cle: "quiz", label: "Quiz", moduleDb: "QUIZ" },
];

export function moduleParCle(cle) {
  return MODULES.find((m) => m.cle === cle) || null;
}

export const STATUTS = [
  { valeur: "EN_COURS", label: "En cours", couleur: "#dba617" },
  { valeur: "ENVOYEE_BAR", label: "Envoyée (bar)", couleur: "#2271b1" },
  { valeur: "PAYEE", label: "Payée", couleur: "#00a32a" },
  { valeur: "ECHOUEE", label: "Échouée", couleur: "#d63638" },
  { valeur: "ANNULEE", label: "Annulée", couleur: "#787c82" },
];

export function statutInfo(valeur) {
  return STATUTS.find((s) => s.valeur === valeur) || { valeur, label: valeur, couleur: "#787c82" };
}
