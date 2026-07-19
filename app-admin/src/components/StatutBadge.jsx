import { statutInfo } from "../config";

export default function StatutBadge({ statut }) {
  const info = statutInfo(statut);
  return (
    <span className="badge" style={{ background: info.couleur }}>
      {info.label}
    </span>
  );
}
