# Bornes Bowling - Phase 1 (validée) + Phase 2 (en cours)

Borne ↔ Backend ↔ Bot Conqueror (Phase 1, validée) + BDD PostgreSQL, catalogue/commandes
bar, Back-Office admin (Phase 2 et suivantes). Voir `Roadmap_Projet_Bornes.txt` pour le
détail phase par phase.

Dossiers : `backend/` (API Node.js), `app-borne/` (borne, React/Capacitor à terme),
`app-admin/` (Back-Office), `bot/` (automatisation Conqueror, Python), `test-client/`
(page de test Phase 1, sans build).

## Architecture

Tout tourne en local (plus de backend en ligne : l'ancien domaine n'existe plus).

```
PC backend / démo                                              PC Conqueror
[app-borne :5173] --WebSocket/HTTP--> [Backend Node.js :3000] <--WebSocket-- [bot/conqueror_bot.py]
[app-admin :5174] -------------------------^        ^                        (mode REEL par défaut,
[test-client]     --------------------------------- '                         SERVEUR_URL=http://<IP PC backend>:3000)
```

- Backend, borne et admin tournent sur le PC backend (démo).
- Le bot tourne SUR le PC Conqueror et rejoint le backend via le réseau local :
  `http://<IP du PC backend>:3000`.
- Une tablette du même Wi-Fi peut ouvrir la borne via `http://<IP du PC backend>:5173` :
  elle vise alors automatiquement le backend `http://<IP du PC backend>:3000`.

## Démo sur le PC backend

Prérequis (une fois) :
- `backend/.env` avec `DATABASE_URL` (Neon), `JWT_SECRET`, `PORT=3000` (cf.
  `backend/.env.example`).
- `npm install` dans `backend/`, `app-borne/` et `app-admin/`, puis `npx prisma generate`
  dans `backend/`.

Lancement (cmd, une seule commande, ouvre 3 fenêtres) :

```
cd /d <dossier du projet> && start "Backend" cmd /k "cd backend && npm start" && start "Borne" cmd /k "cd app-borne && npm run dev -- --host" && start "Admin" cmd /k "cd app-admin && npm run dev"
```

`--host` sur la borne : la rend accessible depuis une tablette du même Wi-Fi. Vite
affiche les URL (borne en `:5173`, admin sur le port suivant libre, en général `:5174`).

Pare-feu : autoriser le port **3000 entrant** sur le PC backend (sinon le bot et les
tablettes ne le joignent pas), et `5173` pour une tablette. IP du PC backend : `ipconfig`
→ "Adresse IPv4".

Premier lancement : `node prisma/seed.js` dans `backend/` crée le compte admin
(`admin@bowling.local`, mot de passe affiché une seule fois).

## Bot Conqueror (sur le PC Conqueror)

Prérequis (une fois) : Python 3.10+ (cocher "Add to PATH" à l'install).

```
cd bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

URL du backend, au choix (ordre de priorité : argument > variable d'env > `http://localhost:3000`) :

- Argument : `py conqueror_bot.py http://10.30.0.187:3000`
- PowerShell :
  ```powershell
  $env:SERVEUR_URL="http://IP:3000"
  py conqueror_bot.py
  ```
- cmd :
  ```
  set SERVEUR_URL=http://IP:3000
  py conqueror_bot.py
  ```

Le bot affiche l'URL utilisée ; si le backend est injoignable, il l'indique et réessaie
toutes les 5 s (vérifier que le backend tourne, l'IP, et le pare-feu du PC backend).

**Le bot démarre en mode REEL par défaut** (interagit vraiment avec Conqueror =
PRODUCTION). Pour une démo sans toucher à Conqueror : `SIMULATION_MODE=true`
(PowerShell : `$env:SIMULATION_MODE="true"` ; cmd : `set SIMULATION_MODE=true`) - le bot
se connecte et reçoit les commandes mais se contente de les logger.
`CONFIRMATION_MANUELLE=true` demande une confirmation avant chaque clic réel (désactivée
par défaut). cf. `bot/conqueror_bot.py` pour le détail du parcours automatisé.

Test rapide : `test-client/index.html` (ouvert en `file://` sur le PC backend, il vise
`http://localhost:3000`) → "Nouvelle Partie" → le terminal du bot doit logger l'action.

## Si ça ne marche pas

- **"Bot : déconnecté" persistant** → vérifier que `py conqueror_bot.py` tourne et
  affiche "connecté" ; sinon vérifier `SERVEUR_URL` (IP du PC backend via `ipconfig`) et
  le pare-feu (port 3000 entrant sur le PC backend).
- **Résultat `bot_indisponible`** → le bot n'est pas enregistré côté serveur, le relancer.
- **`vite` / `npm start` non reconnu** → `npm install` pas encore fait dans le dossier
  concerné (`backend/` ou `app-admin/`).
- **401 sur app-admin après login** → `JWT_SECRET` absent ou différent entre le moment du
  login et celui de la requête (ex: serveur redémarré avec une autre valeur) - se
  reconnecter suffit.
- **Rien ne se passe / erreur réseau** → F12 → onglet Console/Network pour voir l'erreur
  exacte, vérifier `SERVEUR_URL` / `VITE_SERVEUR_URL`.
