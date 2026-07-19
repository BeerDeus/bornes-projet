import { statutInfo } from "../config";

export default function StatutBadge({ statut }) {
  const info = statutInfo(statut);
  return (
    <span className="badge" style={{ "--badge-couleur": info.couleur }}>
      <span className="badge-point" />
      {info.label}
    </span>
  );
}
