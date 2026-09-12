// Contexte auth Back-Office - cf. services/auth.js pour la logique
// login/vérification, services/sessionStorage.js pour la persistance.
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  connexion as connexionApi,
  deconnexion as deconnexionApi,
  obtenirUtilisateur,
  verifierSession,
} from "./services/auth";
import { EVENEMENT_SESSION_EXPIREE } from "./services/sessionStorage";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Hydratation synchrone depuis localStorage (pas un simple `null` initial)
  // pour éviter un flash "non connecté -> connecté" au chargement si une
  // session valide existe déjà - vérifiée ensuite auprès du serveur (cf.
  // useEffect ci-dessous), mais l'UI n'a pas besoin d'attendre ça pour
  // afficher le bon état la plupart du temps.
  const [utilisateur, setUtilisateur] = useState(obtenirUtilisateur);
  const [verificationEnCours, setVerificationEnCours] = useState(true);

  useEffect(() => {
    let annule = false;
    verifierSession().then((u) => {
      if (!annule) {
        setUtilisateur(u);
        setVerificationEnCours(false);
      }
    });
    return () => {
      annule = true;
    };
  }, []);

  useEffect(() => {
    // cf. sessionStorage.js : un 401 en cours de navigation (token expiré,
    // révoqué) vide la session côté stockage - ce listener resynchronise
    // immédiatement le contexte React, sinon l'UI resterait "connectée en
    // apparence" jusqu'au prochain rechargement.
    function surSessionExpiree() {
      setUtilisateur(null);
    }
    window.addEventListener(EVENEMENT_SESSION_EXPIREE, surSessionExpiree);
    return () => window.removeEventListener(EVENEMENT_SESSION_EXPIREE, surSessionExpiree);
  }, []);

  const connecter = useCallback(async (email, motDePasse) => {
    const u = await connexionApi(email, motDePasse);
    setUtilisateur(u);
    return u;
  }, []);

  const deconnecter = useCallback(() => {
    deconnexionApi();
    setUtilisateur(null);
  }, []);

  return (
    <AuthContext.Provider value={{ utilisateur, verificationEnCours, connecter, deconnecter }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth() doit être appelé sous <AuthProvider>.");
  return ctx;
}
