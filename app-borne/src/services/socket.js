// Socket.io - canal temps réel borne <-> backend <-> bot Conqueror (Phase 1)
// + diffusion des mises à jour de commande bar (Phase 2, événement
// "commande_maj"). Un seul socket partagé dans toute l'app (singleton),
// avec reconnexion automatique (comportement par défaut de socket.io-client,
// cf. CDC 2.2 - reconnexion avec backoff).
import { io } from "socket.io-client";
import { SERVEUR_URL } from "../config";

export const socket = io(SERVEUR_URL, {
  autoConnect: true,
  reconnection: true,
  reconnectionDelay: 500,
  reconnectionDelayMax: 5000,
});
