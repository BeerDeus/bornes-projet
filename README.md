# Phase 1 - Preuve de Concept (Borne ↔ Backend ↔ Bot Conqueror)

Ce dossier contient le code testé pour la Phase 1 de la Roadmap.

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

Le parcours automatisé se fait en 3 étapes, **chacune avec sa propre confirmation** :

1. `$env:SIMULATION_MODE="false"` puis `python conqueror_bot.py` — tu dois voir
   `ATTENTION : mode réel actif...`.
2. Déclencher le test depuis `index.html`. Le bot va, à chaque étape, remplir/cliquer
   puis attendre ta validation en console avant de continuer :
   - **Étape 1/3** : remplit "Référence" avec "Test" → demande confirmation avant de
     cliquer "Sple Partie" (ouvre la piste).
   - **Étape 2/3** : demande confirmation avant de cliquer "Nbre joueurs".
   - **Étape 3/3** : demande confirmation avant de sélectionner le nombre de joueurs
     (valeur envoyée par la borne, `nbJoueurs`) et de cliquer "OK".
3. À chaque prompt, vérifie sur l'écran Conqueror que l'état correspond bien à ce qui
   est annoncé **avant** de taper `o`. Toute autre touche annule cette étape sans rien
   exécuter (les étapes précédentes déjà validées restent, elles, acquises).
4. Note : la sélection de la piste (combo "Ressource") n'est pas encore automatisée —
   la piste actuellement sélectionnée par défaut dans Conqueror est utilisée.

Une fois plusieurs tests réels validés sans souci, `CONFIRMATION_MANUELLE=false`
permettra de retirer ces confirmations (à faire consciemment, pas par défaut).

## Pour tester depuis une vraie tablette Android

Comme le backend est public (Hostinger), `test-client/index.html` fonctionne depuis
n'importe quel appareil avec un navigateur (tablette, téléphone), pas besoin d'être sur
le même réseau Wi-Fi que le PC Conqueror. Seul le bot doit rester sur ce PC.

## Si ça ne marche pas

- **"Bot : déconnecté" persistant** → vérifier que le terminal du bot est bien lancé
  et affiche "connecté".
- **Résultat `bot_indisponible`** → le bot n'est pas enregistré auprès du serveur,
  relancer `python conqueror_bot.py`.
- **Rien ne se passe au clic** → ouvrir la console du navigateur (F12) pour voir les
  erreurs, vérifier que `SERVEUR_URL` pointe vers la bonne adresse.
