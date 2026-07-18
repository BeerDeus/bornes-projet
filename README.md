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

1. Ouvrir Conqueror et repérer les vrais identifiants des boutons ("Nouvelle Partie",
   champ de saisie du nom...) avec l'inspecteur pywinauto :
   ```powershell
   python -m pywinauto.actionlogger
   ```
   ou en important `Application(backend="uia").connect(...).print_control_identifiers()`
   dans un script Python temporaire, Conqueror étant ouvert.
2. Compléter les `TODO` dans `bot/conqueror_bot.py` (fonction
   `ouvrir_nouvelle_partie_reelle`) avec les vrais sélecteurs trouvés.
3. Relancer le bot avec `SIMULATION_MODE=false` :
   ```powershell
   $env:SIMULATION_MODE="false"
   python conqueror_bot.py
   ```
4. Refaire le test depuis `index.html`. Cette fois, ça doit réellement ouvrir une
   piste dans Conqueror.

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
