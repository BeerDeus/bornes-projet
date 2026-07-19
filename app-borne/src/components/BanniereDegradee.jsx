// Bannière "Service momentanément indisponible" (CDC 2.1 - mode dégradé).
// Affichée dès que le socket vers le backend est coupé - bloque la
// composition de commandes financières plutôt que de laisser l'utilisateur
// arriver au bout d'un parcours qui ne pourra jamais aboutir.
import { useSelector } from "react-redux";
import { selectionnerServiceIndisponible } from "../store/connectionSlice";

export default function BanniereDegradee() {
  const indisponible = useSelector(selectionnerServiceIndisponible);
  if (!indisponible) return null;

  return (
    <div style={{
      background: "#991b1b", color: "white", padding: "10px 16px",
      textAlign: "center", fontWeight: "bold", fontSize: 14,
    }}>
      Service momentanément indisponible — reconnexion en cours... Aucune commande ne peut être validée pour le moment.
    </div>
  );
}
