# Bornes Bowling - Phase 1 (validée) + Phase 2 (en cours)

Ce dossier contient le code Phase 1 (Borne ↔ Backend ↔ Bot Conqueror, validée)
et le début de la Phase 2 (BDD PostgreSQL + API catalogue/commandes bar,
app-borne React). Voir `Roadmap_Projet_Bornes.txt` pour le détail.

Contexte Phase 2 : pas encore d'accès à l'API Trivec ni à une tablette
Android à ce jour. `backend/` et `app-borne/` sont développés et testables
via navigateur ; l'intégration Trivec tourne en mode mock (articles bar
temporaires en base) en attendant l'accès réel - voir `backend/README.md`
(à créer si besoin) et `backend/src/trivec/client.js`.

## Architecture actuelle

```
[index.html dans un navigateur]  --WebSocket-->  [Backend Node.js sur Hostinger]  --WebSocket-->  [bot/conqueror_bot.py]
      (simule la borne, n'importe où)              https://bowling.m2s-photo.fr      (mode SIMULATION par défaut,
                                                     (déjà en ligne, rien à lancer)     ne touche pas à Conqueror,
                                                                                        à lancer SUR le PC Conqueror)
```

Le backend est déployé sur Hostinger (repo GitHub → dossier `site-hostinger`, déploiement
automatique à chaque `git push`). Tu n'as **plus besoin de le lancer localement**. Seul le
bot doit tourner sur le PC Conqueror (pywinauto pilote l'UI Windows en local, obligatoire).

Note architecture : héberger le backend sur Hostinger simplifie les tests (accessible de
partout), au prix d'une dépendance à internet pour le fonctionnement des bornes en prod —
géré par le mode dégradé prévu au Cahier des Charges (section 4).

## Étapes

### 1. Installer les prérequis sur le PC Conqueror (une seule fois)

- Python 3.10+ : https://www.python.org/downloads/ (cocher "Add to PATH" à l'installation)

### 2. Lancer le bot (mode simulation, sans risque)

Dans un terminal (PowerShell), dans `bot/` :

```powershell
cd bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python conqueror_bot.py
```

Par défaut `SIMULATION_MODE=true` : le bot se connecte réellement mais ne touche pas à
Conqueror, il se contente de logger l'action. Tu dois voir :
`[bot] connecté à https://bowling.m2s-photo.fr (mode SIMULATION)`

### 3. Déclencher le test depuis la "borne"

Ouvrir `test-client/index.html` directement dans un navigateur (double-clic sur le
fichier). Cliquer sur **"Nouvelle Partie"**.

Résultat attendu :
- Le statut "Bot : connecté" s'affiche en haut.
- Le terminal du bot affiche `[SIMULATION] Ouverture piste + saisie nom 'Test'...`.
- La page affiche `Résultat : {"succes":true,"piste":3,...}`.

Si tout ça fonctionne : le canal temps réel borne → backend → bot est validé de bout
en bout. C'est le livrable de la Phase 1 (cf. Roadmap).

### 4. Passer en mode réel (seulement une fois le test simulé validé)

Les identifiants réels de Conqueror ont déjà été relevés (via `bot/inspect_conqueror.py`,
écran "Liste d'attente") et intégrés dans `ouvrir_nouvelle_partie_reelle`.

**Important : Conqueror ici est le système de PRODUCTION**, pas un environnement de
test. Par sécurité, le mode réel demande une confirmation manuelle dans le terminal
avant chaque clic effectif (`CONFIRMATION_MANUELLE=true` par défaut) — rien ne se passe
tant que tu ne tapes pas "o". Idéalement, fais ce premier essai réel **hors heures
d'ouverture / hors événement**, pas un samedi soir.

Le parcours automatisé (validé en conditions réelles, cf. `bot/conqueror_bot.py` et
Roadmap Phase 1) :

1. Remplit "Référence" puis clique "Sple Partie" (ouvre la piste, écran LaneControl).
2. Clique "Nbre joueurs" → dialogue "dlg" → sélectionne le nombre (crée des
   placeholders "joueur1".."joueurN").
3. Pour chaque joueur (`data.joueurs`) : renomme son placeholder (`set_text`, pas de
   frappe clavier simulée - Conqueror filtre l'injection clavier) + bumpers si fourni.
4. Pour chaque joueur : clique sa cellule "Parties" → fenêtre PDV dédiée → sélectionne
   son tarif (`CE` / `1` / `2` / `3` / `2+1`) et son nombre de parties.
5. Optionnel (`data.payer: true`) : clique "Payer" → "Paye" (validé sur tarif CE/0€
   uniquement pour l'instant).

Non géré pour l'instant (prévu en Phase 4, cf. Cahier des Charges section 3) :
sélection de la piste (la piste par défaut est utilisée), mode de paiement TPE avant
"Paye" (seul le cas 0€ est validé).

## Pour tester depuis une vraie tablette Android

Comme le backend est public (Hostinger), `test-client/index.html` (Phase 1) et
`app-borne/` (Phase 2, catalogue bar + panier + mêmes scénarios bowling) fonctionnent
depuis n'importe quel appareil avec un navigateur (tablette, téléphone), pas besoin
d'être sur le même réseau Wi-Fi que le PC Conqueror. Seul le bot doit rester sur ce PC.

## Si ça ne marche pas

- **"Bot : déconnecté" persistant** → vérifier que le terminal du bot est bien lancé
  et affiche "connecté".
- **Résultat `bot_indisponible`** → le bot n'est pas enregistré auprès du serveur,
  relancer `python conqueror_bot.py`.
- **Rien ne se passe au clic** → ouvrir la console du navigateur (F12) pour voir les
  erreurs, vérifier que `SERVEUR_URL` pointe vers la bonne adresse.
