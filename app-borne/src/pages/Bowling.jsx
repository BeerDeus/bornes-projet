// Module Bowling - parcours client complet (Phase 4, cf. demande Beer
// 2026-07-19) : nb joueurs -> nb parties -> prénoms+bumpers -> récap
// (code avantage + CGV) -> paiement (SIMULÉ pour l'instant, Phase 3 pas
// encore faite) -> exécution bot Conqueror -> récap final avec numéro de
// commande (BOxxx, cf. backend/src/numeroCommande.js).
//
// Pour les scénarios de test bruts du bot (utilisés pendant le dev), voir
// BowlingDebug.jsx (lien en bas de la première étape).
import { useState } from "react";
import { useSelector } from "react-redux";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { selectionnerServiceIndisponible } from "../store/connectionSlice";

const NB_JOUEURS_MAX = 8; // capacité physique habituelle d'une piste
const NB_PARTIES_MAX = 5;

function Stepper({ valeur, onChange, min, max }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16, justifyContent: "center" }}>
      <button
        onClick={() => onChange(Math.max(min, valeur - 1))}
        disabled={valeur <= min}
        style={stylesBouton.stepper}
      >
        −
      </button>
      <span style={{ fontSize: 32, fontWeight: "bold", minWidth: 48, textAlign: "center" }}>{valeur}</span>
      <button
        onClick={() => onChange(Math.min(max, valeur + 1))}
        disabled={valeur >= max}
        style={stylesBouton.stepper}
      >
        +
      </button>
    </div>
  );
}

export default function Bowling() {
  const serviceIndisponible = useSelector(selectionnerServiceIndisponible);

  const [etape, setEtape] = useState("nbJoueurs"); // nbJoueurs | nbParties | joueurs | recap | paiement | resultat
  const [nbJoueurs, setNbJoueurs] = useState(1);
  const [nbParties, setNbParties] = useState(1);
  const [joueurs, setJoueurs] = useState([{ prenom: "", bumpers: false }]);
  const [codeAvantage, setCodeAvantage] = useState("");
  const [cgvAcceptees, setCgvAcceptees] = useState(false);
  const [erreurEnvoi, setErreurEnvoi] = useState(null);
  const [resultatCommande, setResultatCommande] = useState(null);

  function allerA(nomEtape) {
    setErreurEnvoi(null);
    setEtape(nomEtape);
  }

  function validerNbJoueurs() {
    // Redimensionne le tableau des joueurs sur le nouveau nombre, en gardant
    // ce qui était déjà saisi si l'utilisateur revient en arrière.
    setJoueurs((precedents) => {
      const suivants = [...precedents];
      while (suivants.length < nbJoueurs) suivants.push({ prenom: "", bumpers: false });
      return suivants.slice(0, nbJoueurs);
    });
    allerA("nbParties");
  }

  function modifierJoueur(index, champs) {
    setJoueurs((precedents) => precedents.map((j, i) => (i === index ? { ...j, ...champs } : j)));
  }

  function tousLesPrenomsRemplis() {
    return joueurs.every((j) => j.prenom.trim().length > 0);
  }

  async function payer() {
    allerA("paiement");
    try {
      const commande = await api.creerCommandeBowling({
        nbParties,
        joueurs: joueurs.map((j) => ({ prenom: j.prenom.trim(), bumpers: j.bumpers })),
        codeAvantage: codeAvantage.trim() || undefined,
        cgvAcceptees,
      });
      setResultatCommande(commande);
      setEtape("resultat");
    } catch (exc) {
      setErreurEnvoi(exc.message);
      setEtape("recap");
    }
  }

  function nouvelleCommande() {
    setNbJoueurs(1);
    setNbParties(1);
    setJoueurs([{ prenom: "", bumpers: false }]);
    setCodeAvantage("");
    setCgvAcceptees(false);
    setResultatCommande(null);
    setErreurEnvoi(null);
    setEtape("nbJoueurs");
  }

  return (
    <div style={{ padding: 16, maxWidth: 480, margin: "0 auto" }}>
      <p><Link to="/">← Accueil</Link></p>
      <h2 style={{ textAlign: "center" }}>Bowling</h2>

      {etape === "nbJoueurs" && (
        <div>
          <p style={{ textAlign: "center" }}>Combien de joueurs ?</p>
          <Stepper valeur={nbJoueurs} onChange={setNbJoueurs} min={1} max={NB_JOUEURS_MAX} />
          <button style={{ ...stylesBouton.principal, marginTop: 32 }} onClick={validerNbJoueurs}>
            Suivant
          </button>
          <p style={{ textAlign: "center", marginTop: 24 }}>
            <Link to="/bowling-debug" style={{ fontSize: 12, color: "#999" }}>
              Tester rapidement le bot (scénarios prédéfinis)
            </Link>
          </p>
        </div>
      )}

      {etape === "nbParties" && (
        <div>
          <p style={{ textAlign: "center" }}>Combien de parties ?</p>
          <Stepper valeur={nbParties} onChange={setNbParties} min={1} max={NB_PARTIES_MAX} />
          <div style={{ display: "flex", gap: 12, marginTop: 32 }}>
            <button style={stylesBouton.secondaire} onClick={() => allerA("nbJoueurs")}>← Retour</button>
            <button style={stylesBouton.principal} onClick={() => allerA("joueurs")}>Suivant</button>
          </div>
        </div>
      )}

      {etape === "joueurs" && (
        <div>
          <p>Prénom de chaque joueur :</p>
          {joueurs.map((joueur, index) => (
            <div key={index} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <input
                type="text"
                placeholder={`Joueur ${index + 1}`}
                value={joueur.prenom}
                onChange={(e) => modifierJoueur(index, { prenom: e.target.value })}
                style={{ flex: 1, padding: 10, fontSize: 16, borderRadius: 8, border: "1px solid #ddd" }}
              />
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, whiteSpace: "nowrap" }}>
                <input
                  type="checkbox"
                  checked={joueur.bumpers}
                  onChange={(e) => modifierJoueur(index, { bumpers: e.target.checked })}
                />
                Barrières
              </label>
            </div>
          ))}
          <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
            <button style={stylesBouton.secondaire} onClick={() => allerA("nbParties")}>← Retour</button>
            <button
              style={stylesBouton.principal}
              disabled={!tousLesPrenomsRemplis()}
              onClick={() => allerA("recap")}
            >
              Suivant
            </button>
          </div>
        </div>
      )}

      {etape === "recap" && (
        <div>
          <h3>Récapitulatif</h3>
          <ul>
            {joueurs.map((j, i) => (
              <li key={i}>
                {j.prenom} - {nbParties} partie{nbParties > 1 ? "s" : ""}
                {j.bumpers ? " - barrières" : ""}
              </li>
            ))}
          </ul>

          <label style={{ display: "block", marginTop: 16, fontSize: 14 }}>
            Code Pass CE (optionnel)
            <input
              type="text"
              value={codeAvantage}
              onChange={(e) => setCodeAvantage(e.target.value)}
              placeholder="Scan à venir - saisie manuelle pour l'instant"
              style={{ width: "100%", padding: 10, fontSize: 16, borderRadius: 8, border: "1px solid #ddd", marginTop: 6 }}
            />
          </label>

          <label style={{ display: "flex", alignItems: "flex-start", gap: 8, marginTop: 20, fontSize: 13 }}>
            <input
              type="checkbox"
              checked={cgvAcceptees}
              onChange={(e) => setCgvAcceptees(e.target.checked)}
              style={{ marginTop: 3 }}
            />
            J'accepte les conditions générales de vente (texte à finaliser).
          </label>

          {erreurEnvoi && (
            <p style={{ color: "#991b1b", marginTop: 12 }}>Erreur : {erreurEnvoi}</p>
          )}
          {serviceIndisponible && (
            <p style={{ color: "#991b1b", marginTop: 12 }}>Service indisponible - réessaie dans un instant.</p>
          )}

          <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
            <button style={stylesBouton.secondaire} onClick={() => allerA("joueurs")}>← Retour</button>
            <button
              style={{ ...stylesBouton.principal, background: "#16a34a" }}
              disabled={!cgvAcceptees || serviceIndisponible}
              onClick={payer}
            >
              Payer (simulé)
            </button>
          </div>
        </div>
      )}

      {etape === "paiement" && (
        <p style={{ textAlign: "center", marginTop: 40 }}>Paiement en cours (simulé)...</p>
      )}

      {etape === "resultat" && resultatCommande && (
        <div style={{ textAlign: "center" }}>
          <h3>Commande {resultatCommande.numero}</h3>
          <p>Statut : {resultatCommande.statut}</p>
          {resultatCommande.botSucces === true && (
            <p style={{ color: "#166534" }}>
              Partie créée sur la piste {resultatCommande.botPiste ?? "?"}.
            </p>
          )}
          {resultatCommande.botSucces === false && (
            <p style={{ color: "#991b1b" }}>
              Le bot n'a pas pu créer la partie automatiquement ({resultatCommande.botErreur}).
              Merci de te présenter à l'accueil.
            </p>
          )}
          <pre style={{ textAlign: "left", background: "#f3f4f6", padding: 12, borderRadius: 8, fontSize: 12, whiteSpace: "pre-wrap" }}>
            {JSON.stringify(resultatCommande, null, 2)}
          </pre>
          <button style={stylesBouton.principal} onClick={nouvelleCommande}>Nouvelle commande</button>
        </div>
      )}
    </div>
  );
}

const stylesBouton = {
  principal: {
    flex: 1, padding: 16, fontSize: 16, borderRadius: 10, border: "none",
    background: "#2563eb", color: "white", cursor: "pointer",
  },
  secondaire: {
    flex: 1, padding: 16, fontSize: 16, borderRadius: 10, border: "1px solid #ddd",
    background: "white", color: "#111", cursor: "pointer",
  },
  stepper: {
    width: 56, height: 56, fontSize: 28, borderRadius: "50%", border: "none",
    background: "#2563eb", color: "white", cursor: "pointer",
  },
};
