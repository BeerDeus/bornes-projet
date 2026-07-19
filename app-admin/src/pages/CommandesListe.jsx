// Liste des commandes d'un module, cf. backend/src/routes/adminCommandes.js
// (GET /api/admin/commandes?module=...). Clic sur une ligne -> page détail
// dédiée (CommandeDetail.jsx), cf. demande Beer 2026-07-19.
import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import { moduleParCle, STATUTS } from "../config";
import StatutBadge from "../components/StatutBadge";
import { formatDate, formatMontant } from "../utils/format";

const TAILLE_PAGE = 20;

export default function CommandesListe() {
  const { module: moduleCle } = useParams();
  const module = moduleParCle(moduleCle);

  const [statutFiltre, setStatutFiltre] = useState("");
  const [page, setPage] = useState(1);
  const [donnees, setDonnees] = useState(null);
  const [erreur, setErreur] = useState(null);
  const [chargement, setChargement] = useState(true);

  // Réinitialise la page quand on change de module ou de filtre statut
  // (sinon "page 3" pourrait rester sélectionnée sur une liste vide).
  useEffect(() => {
    setPage(1);
  }, [moduleCle, statutFiltre]);

  useEffect(() => {
    if (!module) return;
    let annule = false;
    setChargement(true);
    setErreur(null);
    api
      .getCommandes({ module: module.moduleDb, statut: statutFiltre, page, pageSize: TAILLE_PAGE })
      .then((res) => {
        if (!annule) setDonnees(res);
      })
      .catch((exc) => {
        if (!annule) setErreur(exc);
      })
      .finally(() => {
        if (!annule) setChargement(false);
      });
    return () => {
      annule = true;
    };
  }, [module, statutFiltre, page]);

  if (!module) return <Navigate to="/bowling/commandes" replace />;

  const totalPages = donnees ? Math.max(1, Math.ceil(donnees.total / donnees.pageSize)) : 1;

  return (
    <>
      <div className="fil-ariane">{module.label}</div>
      <div className="entete-page">
        <h1>Commandes — {module.label}</h1>
      </div>

      <div className="barre-filtres">
        <select value={statutFiltre} onChange={(e) => setStatutFiltre(e.target.value)}>
          <option value="">Tous les statuts</option>
          {STATUTS.map((s) => (
            <option key={s.valeur} value={s.valeur}>
              {s.label}
            </option>
          ))}
        </select>
        {donnees && <span style={{ color: "var(--text-muted)", fontSize: 13 }}>{donnees.total} commande(s)</span>}
      </div>

      {chargement && (
        <div className="etat-chargement">
          <span className="spinner" />
          Chargement…
        </div>
      )}
      {erreur && <div className="etat-erreur">Erreur de chargement : {erreur.message}</div>}

      {!chargement && !erreur && donnees && donnees.commandes.length === 0 && (
        <div className="etat-vide">Aucune commande pour ce module{statutFiltre ? " avec ce statut" : ""}.</div>
      )}

      {!chargement && !erreur && donnees && donnees.commandes.length > 0 && (
        <>
          <table className="liste">
            <thead>
              <tr>
                <th>Numéro</th>
                <th>Statut</th>
                <th>Total</th>
                <th>Moyen paiement</th>
                <th>Créée le</th>
              </tr>
            </thead>
            <tbody>
              {donnees.commandes.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link className="lien-numero" to={`/${moduleCle}/commandes/${c.id}`}>
                      {c.numero || c.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td>
                    <StatutBadge statut={c.statut} />
                  </td>
                  <td>{formatMontant(c.totalCentimes)}</td>
                  <td>{c.moyenPaiement || "—"}</td>
                  <td>{formatDate(c.creeLe)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="pagination">
            <button type="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              ← Précédent
            </button>
            <span>
              Page {page} / {totalPages}
            </span>
            <button type="button" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Suivant →
            </button>
          </div>
        </>
      )}
    </>
  );
}
