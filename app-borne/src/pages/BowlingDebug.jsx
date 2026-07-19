// Scénarios de test bruts pour le bot Conqueror (Phase 1, porté depuis
// test-client/index.html) - court-circuite le wizard client (cf. Bowling.jsx,
// le vrai parcours client Phase 4) pour taper directement des scénarios
// prédéfinis pendant le développement du bot (7 joueurs, tarifs CE, etc.).
// Gardé comme page de debug séparée : le parcours client normal, lui, passe
// par POST /api/commandes-bowling (numéro BOxxx, paiement simulé, etc.).
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { Link } from "react-router-dom";
import { socket } from "../services/socket";

const SCENARIOS = [
  {
    id: "2joueurs",
    label: "Nouvelle partie (2 joueurs)",
    commande: {
      nom: "Test",
      joueurs: [
        { nom: "Alice", tarif: "1" },
        { nom: "Bob", bumpers: true, tarif: "CE" },
      ],
    },
  },
  {
    id: "7joueurs",
    label: "Test 7 joueurs (2 parties chacun, 2 en CE)",
    commande: {
      nom: "Test7",
      joueurs: [
        { nom: "Alice", tarif: "2", parties: 2 },
        { nom: "Bob", tarif: "CE", parties: 2 },
        { nom: "Carla", tarif: "2", parties: 2 },
        { nom: "David", tarif: "2", parties: 2 },
        { nom: "Emma", tarif: "CE", parties: 2 },
        { nom: "Felix", tarif: "2", parties: 2 },
        { nom: "Gina", tarif: "2", parties: 2 },
      ],
    },
  },
  {
    id: "1joueurPaye",
    label: "1 joueur CE + Payer",
    commande: {
      nom: "TestPaye",
      payer: true,
      joueurs: [{ nom: "Alice", tarif: "CE" }],
    },
  },
];

export default function BowlingDebug() {
  const botConnecte = useSelector((s) => s.connexion.botConnecte);
  const [journal, setJournal] = useState([]);
  const [envoiEnCours, setEnvoiEnCours] = useState(false);

  useEffect(() => {
    const surResultat = (resultat) => {
      ajouterJournal("Résultat : " + JSON.stringify(resultat));
      setEnvoiEnCours(false);
    };
    socket.on("nouvelle_partie_resultat", surResultat);
    return () => socket.off("nouvelle_partie_resultat", surResultat);
  }, []);

  function ajouterJournal(ligne) {
    setJournal((j) => [...j, ligne]);
  }

  function envoyer(scenario) {
    setEnvoiEnCours(true);
    ajouterJournal(`Envoi commande "${scenario.label}"...`);
    socket.emit("nouvelle_partie", scenario.commande);
  }

  return (
    <div style={{ padding: 16, maxWidth: 560 }}>
      <p><Link to="/bowling">← Bowling</Link> · <Link to="/">Accueil</Link></p>
      <h2>Bowling - scénarios de test (bot Conqueror)</h2>
      <p>Bot : {botConnecte ? "connecté" : "déconnecté"}</p>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {SCENARIOS.map((scenario) => (
          <button
            key={scenario.id}
            disabled={envoiEnCours || !botConnecte}
            onClick={() => envoyer(scenario)}
            style={{ padding: 16, fontSize: 16, borderRadius: 10, border: "none", background: "#2563eb", color: "white" }}
          >
            {scenario.label}
          </button>
        ))}
      </div>

      <div style={{ marginTop: 24, background: "#f3f4f6", padding: 12, borderRadius: 8, fontFamily: "monospace", fontSize: 13, whiteSpace: "pre-wrap" }}>
        {journal.length === 0 ? "Aucune commande envoyée." : journal.join("\n")}
      </div>
    </div>
  );
}
