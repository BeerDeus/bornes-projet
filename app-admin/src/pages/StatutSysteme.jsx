// Écran de monitoring Back-Office (cf. demande Beer 2026-07-19, base de la
// Roadmap Phase 5 "statut des bornes et du bot") - interroge
// GET /api/admin/statut (backend/src/routes/adminStatut.js) en polling
// (pas de canal WebSocket dédié à app-admin pour l'instant, plus simple
// qu'ajouter socket.io-client pour un écran de monitoring rafraîchi toutes
// les quelques secondes - largement suffisant pour un usage staff).
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import { formatDate, formatDepuis } from "../utils/format";

const INTERVALLE_MS = 5000;

export default function StatutSysteme() {
  const [donnees, setDonnees] = useState(null);
  const [erreur, setErreur] = useState(null);
  const [dernierRafraichissement, setDernierRafraichissement] = useState(null);
  const [enCours, setEnCours] = useState(true);
  const minuteurRef = useRef(null);

  const rafraichir = useCallback(async () => {
    try {
      const res = await api.getStatut();
      setDonnees(res);
      setErreur(null);
      setDernierRafraichissement(new Date());
    } catch (exc) {
      setErreur(exc);
    } finally {
      setEnCours(false);
    }
  }, []);

  useEffect(() => {
    rafraichir();
    minuteurRef.current = setInterval(rafraichir, INTERVALLE_MS);
    return () => clearInterval(minuteurRef.current);
  }, [rafraichir]);

  return (
    <>
      <div className="fil-ariane">Système</div>
      <div className="entete-page">
        <h1>Statut système</h1>
      </div>

      {enCours && !donnees && (
        <div className="etat-chargement">
          <span className="spinner" />
          Chargement…
        </div>
      )}

      {erreur && !donnees && (
        <div className="etat-erreur">Impossible de contacter le backend : {erreur.message}</div>
      )}

      {donnees && (
        <>
          <div className="statut-grille">
            <div className="carte">
              <div className="statut-carte-titre">Bot Conqueror</div>
              <div className="statut-etat">
                <span className={`statut-point-grand ${donnees.bot.connecte ? "ok" : "down"}`} />
                {donnees.bot.connecte ? "Connecté" : "Déconnecté"}
              </div>
              <div className="statut-detail">
                {donnees.bot.dernierHeartbeat
                  ? `Dernier battement : ${formatDepuis(donnees.bot.dernierHeartbeat)} (${formatDate(donnees.bot.dernierHeartbeat)})`
                  : "Aucun battement reçu depuis le démarrage du serveur."}
              </div>
            </div>

            <div className="carte">
              <div className="statut-carte-titre">Base de données</div>
              <div className="statut-etat">
                <span className={`statut-point-grand ${donnees.bdd.joignable ? "ok" : "down"}`} />
                {donnees.bdd.joignable ? "Joignable" : "Injoignable"}
              </div>
              <div className="statut-detail">
                {donnees.bdd.joignable
                  ? `Temps de réponse : ${donnees.bdd.tempsMs} ms`
                  : donnees.bdd.erreur || "Erreur inconnue"}
              </div>
            </div>
          </div>

          <div className="statut-refresh">
            {erreur ? (
              <span style={{ color: "var(--danger)" }}>
                Dernier rafraîchissement en échec ({erreur.message}) — nouvelle tentative automatique…
              </span>
            ) : (
              <>
                Actualisé {dernierRafraichissement ? formatDepuis(dernierRafraichissement.toISOString()) : "…"} ·
                rafraîchissement auto. toutes les {INTERVALLE_MS / 1000}s
              </>
            )}
            <button type="button" className="bouton-lien" onClick={rafraichir}>
              Actualiser maintenant
            </button>
          </div>
        </>
      )}
    </>
  );
}
