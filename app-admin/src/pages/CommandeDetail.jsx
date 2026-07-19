// Page détail d'une commande, cf. GET /api/admin/commandes/:id
// (backend/src/routes/adminCommandes.js). Le contenu affiché dépend de ce
// que la commande contient réellement (lignes pour Bar, joueurs pour
// Bowling) plutôt que du module déclaré - une commande n'a jamais les deux
// en même temps, cf. schema.prisma.
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../services/api";
import { moduleParCle } from "../config";
import StatutBadge from "../components/StatutBadge";
import { formatDate, formatMontant } from "../utils/format";

export default function CommandeDetail() {
  const { module: moduleCle, id } = useParams();
  const module = moduleParCle(moduleCle);

  const [commande, setCommande] = useState(null);
  const [erreur, setErreur] = useState(null);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    let annule = false;
    setChargement(true);
    setErreur(null);
    api
      .getCommande(id)
      .then((c) => {
        if (!annule) setCommande(c);
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
  }, [id]);

  return (
    <>
      <Link className="retour-lien" to={`/${moduleCle}/commandes`}>
        ← Retour aux commandes {module ? module.label : ""}
      </Link>
      <div className="entete-page">
        <h1>Commande {commande?.numero || (chargement ? "…" : id.slice(0, 8))}</h1>
      </div>

      {chargement && (
        <div className="etat-chargement">
          <span className="spinner" />
          Chargement…
        </div>
      )}
      {erreur && (
        <div className="etat-erreur">
          {erreur.statut === 404 ? "Commande introuvable." : `Erreur de chargement : ${erreur.message}`}
        </div>
      )}

      {!chargement && !erreur && commande && (
        <>
          <div className="carte">
            <div className="grille-detail">
              <div className="champ-detail">
                <dt>Statut</dt>
                <dd>
                  <StatutBadge statut={commande.statut} />
                </dd>
              </div>
              <div className="champ-detail">
                <dt>Total</dt>
                <dd>{formatMontant(commande.totalCentimes)}</dd>
              </div>
              <div className="champ-detail">
                <dt>Moyen de paiement</dt>
                <dd>{commande.moyenPaiement || "—"}</dd>
              </div>
              <div className="champ-detail">
                <dt>Transaction TPE</dt>
                <dd>{commande.transactionTpeId || "—"}</dd>
              </div>
              <div className="champ-detail">
                <dt>Borne</dt>
                <dd>{commande.borneId || "—"}</dd>
              </div>
              <div className="champ-detail">
                <dt>Créée le</dt>
                <dd>{formatDate(commande.creeLe)}</dd>
              </div>
              <div className="champ-detail">
                <dt>Mise à jour le</dt>
                <dd>{formatDate(commande.majLe)}</dd>
              </div>
              {commande.erreur && (
                <div className="champ-detail">
                  <dt>Erreur</dt>
                  <dd style={{ color: "#d63638" }}>{commande.erreur}</dd>
                </div>
              )}
            </div>
          </div>

          {commande.lignes && commande.lignes.length > 0 && (
            <div className="carte">
              <h2 style={{ fontSize: 15, marginTop: 0 }}>Articles</h2>
              <table className="liste">
                <thead>
                  <tr>
                    <th>Produit</th>
                    <th>Quantité</th>
                    <th>Prix unitaire</th>
                    <th>Sous-total</th>
                  </tr>
                </thead>
                <tbody>
                  {commande.lignes.map((l) => (
                    <tr key={l.id}>
                      <td>{l.produit?.nom || "—"}</td>
                      <td>{l.quantite}</td>
                      <td>{formatMontant(l.prixUnitaireCentimes)}</td>
                      <td>{formatMontant(l.prixUnitaireCentimes * l.quantite)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {commande.ticketTrivecId && (
                <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 0 }}>
                  Ticket Trivec : {commande.ticketTrivecId}
                </p>
              )}
            </div>
          )}

          {commande.joueurs && commande.joueurs.length > 0 && (
            <div className="carte">
              <h2 style={{ fontSize: 15, marginTop: 0 }}>Joueurs</h2>
              <table className="liste">
                <thead>
                  <tr>
                    <th>Prénom</th>
                    <th>Bumpers</th>
                    <th>Parties</th>
                  </tr>
                </thead>
                <tbody>
                  {commande.joueurs.map((j) => (
                    <tr key={j.id}>
                      <td>{j.prenom}</td>
                      <td>{j.bumpers ? "Oui" : "Non"}</td>
                      <td>{j.parties}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="grille-detail" style={{ marginTop: 16 }}>
                <div className="champ-detail">
                  <dt>Bot Conqueror</dt>
                  <dd>
                    {commande.botSucces === null || commande.botSucces === undefined
                      ? "—"
                      : commande.botSucces
                        ? "Succès"
                        : `Échec${commande.botErreur ? ` (${commande.botErreur})` : ""}`}
                  </dd>
                </div>
                {commande.botPiste !== null && commande.botPiste !== undefined && (
                  <div className="champ-detail">
                    <dt>Piste</dt>
                    <dd>{commande.botPiste}</dd>
                  </div>
                )}
                {commande.codeAvantageSaisi && (
                  <div className="champ-detail">
                    <dt>Code avantage saisi</dt>
                    <dd>{commande.codeAvantageSaisi}</dd>
                  </div>
                )}
                <div className="champ-detail">
                  <dt>CGV acceptées</dt>
                  <dd>{formatDate(commande.cgvAccepteesLe)}</dd>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </>
  );
}
