// Simule le bouton "Nouvelle Partie" d'une borne (avant que l'app Capacitor existe).
// Se connecte au serveur, envoie une commande, affiche la réponse.

const { io } = require("socket.io-client");

const SERVEUR = process.env.SERVEUR_URL || "http://localhost:3000";
const socket = io(SERVEUR);

socket.on("connect", () => {
  console.log("[tablette-simulateur] connecté, test ping...");
  socket.emit("ping_test", { message: "hello" }, (reponse) => {
    console.log("[tablette-simulateur] pong reçu :", reponse);

    console.log("[tablette-simulateur] envoi commande nouvelle_partie...");
    socket.emit("nouvelle_partie", { nom: "Test", nbJoueurs: 1 });
  });
});

socket.on("nouvelle_partie_resultat", (resultat) => {
  console.log("[tablette-simulateur] résultat reçu :", resultat);
  process.exit(resultat.succes ? 0 : 1);
});

setTimeout(() => {
  console.error("[tablette-simulateur] timeout, aucune réponse du serveur");
  process.exit(1);
}, 15000);
