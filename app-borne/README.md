# App Borne (Phase 2 + Phase 4 Bowling) - Web, testable navigateur

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
- **Bowling** (`/bowling`) : parcours client complet - nb joueurs -> nb parties ->
  prénoms+bumpers par joueur -> récap (encart code Pass CE, non validé pour l'instant +
  case CGV) -> paiement (SIMULÉ, toujours un succès en attendant la Phase 3) -> exécution
  du bot Conqueror -> récap final avec numéro de commande (BOxxx). Envoie vers
  `POST /api/commandes-bowling`.
- **Bowling - debug** (`/bowling-debug`, lien discret en bas de `/bowling`) : les anciens
  scénarios de test bruts (nouvelle partie, 7 joueurs, paiement CE) pour tester le bot
  Conqueror directement, sans passer par le wizard - utile pendant le dev du bot.

## Mode dégradé

Une bannière rouge apparaît dès que le socket vers le backend est coupé
(cf. CDC 2.1) et bloque la validation de commande - pas de commande
financière composée hors ligne.
