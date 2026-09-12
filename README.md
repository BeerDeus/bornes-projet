# Bornes Bowling - Phase 1 (validée) + Phase 2 (en cours)

Borne ↔ Backend ↔ Bot Conqueror (Phase 1, validée) + BDD PostgreSQL, catalogue/commandes
bar, Back-Office admin (Phase 2 et suivantes). Voir `Roadmap_Projet_Bornes.txt` pour le
détail phase par phase.

Dossiers : `backend/` (API Node.js), `app-borne/` (borne, React/Capacitor à terme),
`app-admin/` (Back-Office), `bot/` (automatisation Conqueror, Python), `test-client/`
(page de test Phase 1, sans build).

## Architecture

```
[app-borne / test-client]  --WebSocket/HTTP-->  [Backend Node.js sur Hostinger]  --WebSocket-->  [bot/conqueror_bot.py]
      (n'importe où)                              https://bowling.m2s-photo.fr      (mode SIMULATION par défaut,
                                                    (déjà en ligne, rien à lancer)     à lancer SUR le PC Conqueror)

[app-admin] --------------------------------------------^
      (Back-Office, même backend)
```

Le backend est déployé sur Hostinger (repo `backend_bowling`, déploiement auto à chaque
`git push`) - inutile de le lancer localement pour tester depuis une tablette/un
navigateur pointé dessus. Seul le bot doit tourner en local, sur le PC Conqueror.

## Bot Conqueror

Prérequis (une fois) : Python 3.10+ (cocher "Add to PATH" à l'install).

```powershell
cd bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python conqueror_bot.py
```

Par défaut `SIMULATION_MODE=true` : le bot se connecte réellement mais ne touche pas à
Conqueror (log seulement). Test : ouvrir `test-client/index.html` dans un navigateur,
cliquer "Nouvelle Partie" → le terminal du bot doit logger l'action et la page afficher
`{"succes":true,...}`.

**Mode réel** (Conqueror = PRODUCTION, pas un environnement de test) : demande une
confirmation manuelle par clic (`CONFIRMATION_MANUELLE=true` par défaut) - à faire hors
heures d'ouverture pour le premier essai. cf. `bot/conqueror_bot.py` pour le détail du
parcours automatisé.

## Développement local (backend + app-admin)

Deux terminaux séparés (ex: deux panneaux dans VS Code, `` Ctrl+Shift+` `` pour en ouvrir
un nouveau) :

**Terminal 1 - backend**
```
cd backend
npm install
cp .env.example .env   # DATABASE_URL + JWT_SECRET, cf. backend/README.md
npx prisma generate
node prisma/seed.js    # crée le compte admin, affiche son mot de passe une seule fois
npm start
```

**Terminal 2 - app-admin**
```
cd app-admin
echo VITE_SERVEUR_URL=http://localhost:3000 > .env.local
npm install
npm run dev
```

Puis `http://localhost:5173/connexion` avec `admin@bowling.local` + le mot de passe
affiché par le seed. Rien à pousser sur Hostinger pour tester en local.

## Tester depuis une tablette Android (contre le backend Hostinger)

Comme le backend est public, `test-client/index.html` et `app-borne/` fonctionnent
depuis n'importe quel appareil avec un navigateur, pas besoin d'être sur le Wi-Fi du PC
Conqueror. Seul le bot doit rester sur ce PC.

## Si ça ne marche pas

- **"Bot : déconnecté" persistant** → vérifier que `python conqueror_bot.py` tourne et
  affiche "connecté".
- **Résultat `bot_indisponible`** → le bot n'est pas enregistré côté serveur, le relancer.
- **`vite` / `npm start` non reconnu** → `npm install` pas encore fait dans le dossier
  concerné (`backend/` ou `app-admin/`).
- **401 sur app-admin après login** → `JWT_SECRET` absent ou différent entre le moment du
  login et celui de la requête (ex: serveur redémarré avec une autre valeur) - se
  reconnecter suffit.
- **Rien ne se passe / erreur réseau** → F12 → onglet Console/Network pour voir l'erreur
  exacte, vérifier `SERVEUR_URL` / `VITE_SERVEUR_URL`.
