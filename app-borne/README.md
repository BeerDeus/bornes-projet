# App Borne (Phase 2) - Web, testable navigateur

App React (Vite) qui deviendra l'app tablette une fois encapsulée avec
Capacitor (pas d'accès à une tablette Android pour l'instant, cf. Roadmap).
En attendant, elle tourne dans n'importe quel navigateur et parle au même
backend que le bot Conqueror (Phase 1) + à l'API catalogue/commandes
(Phase 2).

## Lancer en dev

```
npm install
npm run dev
```

Par défaut elle pointe sur le backend Hostinger (bowling.m2s-photo.fr). Pour
pointer sur un backend local, copier `.env.example` en `.env.local` et
ajuster `VITE_SERVEUR_URL`.

## Modules

- **Bar** (`/bar`) : catalogue (depuis la BDD, articles marqués "test" en
  attendant Trivec), panier persistant (localStorage), validation de
  commande -> POST `/api/commandes` -> Trivec (mock).
- **Bowling** (`/bowling`) : reprend les scénarios de test-client/index.html
  (nouvelle partie, 7 joueurs, paiement CE) pour continuer à tester le bot
  Conqueror depuis cette app.

## Mode dégradé

Une bannière rouge apparaît dès que le socket vers le backend est coupé
(cf. CDC 2.1) et bloque la validation de commande - pas de commande
financière composée hors ligne.
