# Backend (Phase 1 + Phase 2 + Phase 4 Bowling)

## Installation

```
cd backend
npm install
cp .env.example .env   # DATABASE_URL + JWT_SECRET (voir sections ci-dessous)
npx prisma generate
npx prisma migrate dev --name init   # crée les tables (déjà fait en prod, inutile de rejouer dessus)
node prisma/seed.js                  # articles bar de test + compte admin (mot de passe affiché une fois)
npm start
```

## Base de données PostgreSQL

Hostinger mutualisé ne fait pas tourner Postgres nativement - BDD hébergée sur Neon
(managé, gratuit). Pour du dev local avec une Postgres à toi à la place :
`docker run -e POSTGRES_PASSWORD=dev -p 5432:5432 postgres:16` puis
`DATABASE_URL="postgresql://postgres:dev@localhost:5432/postgres"`.

**Diagnostic** : `GET /api/sante` et `GET /api/admin/statut` testent la connexion (bornée
à 5s, pour échouer proprement plutôt que de pendre indéfiniment). `bdd.driver` dans
`/api/admin/statut` indique quel driver Prisma tourne réellement (`neon-http` ou
`pg-standard`) - utile pour vérifier qu'un déploiement a bien pris effet.

**Driver Neon HTTP** (`src/db.js`) : si `DATABASE_URL` pointe vers un host `*.neon.tech`,
Prisma passe par `@neondatabase/serverless` + `@prisma/adapter-neon` (requêtes en HTTPS
plutôt qu'en TCP brut sur le port 5432) - certains hébergements mutualisés comme
Hostinger filtrent ce port. Sinon (Postgres locale), driver `pg` standard inchangé.
Nécessite `previewFeatures = ["driverAdapters"]` dans `schema.prisma` (déjà en place) et
donc un `npx prisma generate` après tout `npm install` sur un poste qui ne l'a pas encore.

## Auth Back-Office (`/api/admin/*`)

Auth interne JWT + bcrypt (pas de service externe type Firebase) :

- `POST /api/auth/login { email, motDePasse }` → `{ token, utilisateur }`.
  `GET /api/auth/moi` (`Authorization: Bearer <token>`) vérifie qu'une session est
  toujours valide - utilisé par app-admin au chargement.
- `exigerAuth` (`src/middlewareAuth.js`) protège tout `/api/admin/*` : lecture ouverte à
  tout compte actif, `exigerRole("ADMIN")` en plus sur les mutations de tarifs bowling
  (`adminTarifsBowling.js`).
- `JWT_SECRET` **obligatoire** (le serveur refuse de démarrer sans - pas de valeur par
  défaut en dur dans le code public). Génère une valeur différente par environnement
  (local / Hostinger) avec `node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"`.
  Doit être défini à la fois en local (`.env`) et dans les variables d'environnement
  Hostinger (jamais automatique via `git push`).
- Comptes créés à la main via `prisma/seed.js` (pas d'inscription en self-service) -
  comptes ACCUEIL/BAR à créer en base au besoin.

## Contrainte financière (commande PAYEE ⇒ transactionTpeId)

Le schéma Prisma ne peut pas exprimer nativement une contrainte CHECK conditionnelle (cf.
CDC - "une commande ne peut passer en statut Payée que si l'identifiant de transaction
TPE est valide"). Appliquée côté application (`src/routes/commandes.js`, PATCH
`/commandes/:id/statut`) et côté BDD (migration `20260719140000_add_check_payee_transaction`).

## Trivec (mock)

Pas d'accès à l'API/sandbox Trivec à ce jour. `src/trivec/client.js` expose une interface
stable (`TrivecClient.envoyerCommande`) avec une implémentation mock qui logge le payload
et simule une réponse. Bascule via `TRIVEC_MODE=reel` une fois l'accès obtenu.
`TRIVEC_MOCK_ECHEC=true` force un échec simulé, utile pour tester le cas d'erreur.

## Prisma figé en 5.22.0

`@prisma/client`/`prisma` sont épinglés en dur (pas de `^`) dans `package.json`. Prisma 7
casse `migrate` avec ce schéma (`url` dans `datasource` plus supporté sans
`prisma.config.ts` + adaptateur) - ne pas laisser `npm update`/`npm install` remonter la
version sans retester `migrate`/`generate`.

## Tests

```
node test/commandes.logique.test.js
node test/bowlingCommandes.logique.test.js
node test/adminCommandes.logique.test.js
node test/adminStatut.logique.test.js
node test/adminTarifsBowling.logique.test.js
node test/adminAuth.logique.test.js
node test/tarificationBowling.logique.test.js
```
Tests de logique métier via un mock Prisma en mémoire (`test/_mockPrisma.js`) - pas
besoin d'une vraie Postgres. Un vrai test d'intégration (Postgres réelle) reste à écrire.
