// Monte les écouteurs socket une seule fois et synchronise le store Redux
// (cf. store/connectionSlice.js). Pas de rendu propre : composant de câblage.
import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { socket } from "../services/socket";
import { setSocketConnecte, setBotConnecte } from "../store/connectionSlice";

export default function ConnectionWatcher() {
  const dispatch = useDispatch();

  useEffect(() => {
    const surConnexion = () => dispatch(setSocketConnecte(true));
    const surDeconnexion = () => dispatch(setSocketConnecte(false));
    const surStatutBot = (s) => dispatch(setBotConnecte(!!s.connecte));

    socket.on("connect", surConnexion);
    socket.on("disconnect", surDeconnexion);
    socket.on("bot_status", surStatutBot);

    dispatch(setSocketConnecte(socket.connected));

    return () => {
      socket.off("connect", surConnexion);
      socket.off("disconnect", surDeconnexion);
      socket.off("bot_status", surStatutBot);
    };
  }, [dispatch]);

  return null;
}
