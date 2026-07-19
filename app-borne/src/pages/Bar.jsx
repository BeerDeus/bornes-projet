// Module Bar - catalogue + panier (Phase 2, cf. Roadmap/CDC 3). Le paiement
// réel (TPE/Cashdro) arrive en Phase 3 : ici la commande est envoyée au
// backend qui la transmet à Trivec (mock pour l'instant, cf. backend/src/
// trivec/client.js) sans encaissement.
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link } from "react-router-dom";
import { chargerCatalogue } from "../store/catalogSlice";
import { ajouterProduit, retirerProduit, viderPanier, selectionnerTotalCentimes } from "../store/cartSlice";
import { selectionnerServiceIndisponible } from "../store/connectionSlice";
import { api } from "../services/api";

function formatEuros(centimes) {
  return (centimes / 100).toFixed(2) + " €";
}

export default function Bar() {
  const dispatch = useDispatch();
  const { categories, produits, statut, erreur } = useSelector((s) => s.catalogue);
  const lignesPanier = useSelector((s) => s.panier.lignes);
  const totalCentimes = useSelector(selectionnerTotalCentimes);
  const serviceIndisponible = useSelector(selectionnerServiceIndisponible);
  const [resultatCommande, setResultatCommande] = useState(null);
  const [envoiEnCours, setEnvoiEnCours] = useState(false);

  useEffect(() => {
    dispatch(chargerCatalogue());
  }, [dispatch]);

  async function validerCommande() {
    setEnvoiEnCours(true);
    setResultatCommande(null);
    try {
      const commande = await api.creerCommande({
        borneId: "test-navigateur",
        lignes: lignesPanier.map((l) => ({ produitId: l.produitId, quantite: l.quantite })),
      });
      setResultatCommande(commande);
      if (commande.statut !== "ECHOUEE") dispatch(viderPanier());
    } catch (exc) {
      setResultatCommande({ statut: "ERREUR_RESEAU", erreur: exc.message });
    } finally {
      setEnvoiEnCours(false);
    }
  }

  return (
    <div style={{ display: "flex", gap: 24, padding: 16 }}>
      <div style={{ flex: 2 }}>
        <p><Link to="/">← Accueil</Link></p>
        <h2>Catalogue Bar</h2>
        {statut === "chargement" && <p>Chargement du catalogue...</p>}
        {statut === "erreur" && <p style={{ color: "red" }}>Erreur catalogue : {erreur}</p>}
        {categories.map((cat) => (
          <div key={cat.id} style={{ marginBottom: 16 }}>
            <h3>{cat.nom}</h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {produits.filter((p) => p.categorieId === cat.id).map((produit) => (
                <button
                  key={produit.id}
                  onClick={() => dispatch(ajouterProduit(produit))}
                  style={{ padding: "12px 16px", borderRadius: 10, border: "1px solid #ddd", cursor: "pointer" }}
                >
                  {produit.nom}<br />{formatEuros(produit.prixCentimes)}
                  {produit.estArticleTest && <div style={{ fontSize: 10, color: "#999" }}>(article test)</div>}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div style={{ flex: 1, borderLeft: "1px solid #eee", paddingLeft: 24 }}>
        <h2>Panier</h2>
        {lignesPanier.length === 0 && <p>Panier vide.</p>}
        {lignesPanier.map((ligne) => (
          <div key={ligne.produitId} style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span>{ligne.nom} x{ligne.quantite}</span>
            <span>
              {formatEuros(ligne.prixCentimes * ligne.quantite)}{" "}
              <button onClick={() => dispatch(retirerProduit(ligne.produitId))}>-</button>
            </span>
          </div>
        ))}
        <hr />
        <p><strong>Total : {formatEuros(totalCentimes)}</strong></p>
        <button
          disabled={lignesPanier.length === 0 || envoiEnCours || serviceIndisponible}
          onClick={validerCommande}
          style={{ width: "100%", padding: 14, fontSize: 16, borderRadius: 10, border: "none", background: "#16a34a", color: "white" }}
        >
          {envoiEnCours ? "Envoi..." : "Valider la commande"}
        </button>
        {resultatCommande && (
          <pre style={{ background: "#f3f4f6", padding: 12, marginTop: 12, fontSize: 12, whiteSpace: "pre-wrap" }}>
            {JSON.stringify(resultatCommande, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
