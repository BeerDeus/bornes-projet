// Simule le bot Python (pywinauto) côté Node, pour valider le canal
// backend <-> bot avant d'impliquer le vrai PC Conqueror.
// Le vrai bot (bot/conqueror_bot.py) reproduit exactement ce protocole.

const { io } = require("socket.io-client");

const SERVEUR = process.env.SERVEUR_URL || "http://localhost:3000";
const socket = io(SERVEUR);

socket.on("connect", () => {
  console.log("[bot-simulateur] connecté au serveur, enregistrement...");
  socket.emit("bot_register");

  setInterval(() => socket.emit("bot_heartbeat"), 3000);
});

socket.on("executer_nouvelle_partie", (data, ack) => {
  console.log("[bot-simulateur] commande reçue :", data);
  console.log("[bot-simulateur] (simulation) ouverture piste + saisie nom dans Conqueror...");

  setTimeout(() => {
    ack({ succes: true, piste: 3, nomJoueur: data.nom });
    console.log("[bot-simulateur] partie créée (simulée), acquittement envoyé");
  }, 500);
});

socket.on("disconnect", () => console.log("[bot-simulateur] déconnecté"));
