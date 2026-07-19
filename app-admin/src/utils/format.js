export function formatMontant(centimes) {
  return (Number(centimes || 0) / 100).toLocaleString("fr-FR", {
    style: "currency",
    currency: "EUR",
  });
}

export function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

// "il y a 3s" / "il y a 2 min" / "il y a 1h" - pour le statut système
// (dernier heartbeat du bot), plus lisible qu'un horodatage complet quand ce
// qui compte c'est "est-ce que c'est récent ?".
export function formatDepuis(iso) {
  if (!iso) return "—";
  const secondes = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (secondes < 60) return `il y a ${secondes}s`;
  const minutes = Math.floor(secondes / 60);
  if (minutes < 60) return `il y a ${minutes} min`;
  const heures = Math.floor(minutes / 60);
  return `il y a ${heures} h`;
}
