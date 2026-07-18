"""
Bot RPA Conqueror - Phase 1 (Preuve de Concept)
=================================================
À exécuter SUR le PC qui fait tourner Conqueror (pywinauto pilote l'UI Windows
en local, pas d'accès distant possible).

Mode SIMULATION (par défaut) : le bot se connecte réellement au serveur,
reçoit réellement la commande "nouvelle_partie", mais se contente de logger
l'action au lieu de toucher à Conqueror. Objectif : valider tout le canal de
communication sans aucun risque de saisie erronée dans le logiciel métier
(cf. CDC 2.4 - la dette technique actuelle vient justement d'un bot qui
clique à l'aveugle).

Une fois le mode simulation validé, passer SIMULATION_MODE = False et
compléter les sélecteurs pywinauto marqués TODO ci-dessous, avec Conqueror
ouvert et visible.
"""

import os
import threading
import time

import socketio

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
SERVEUR_URL = os.environ.get("SERVEUR_URL", "https://bowling.m2s-photo.fr")
SIMULATION_MODE = os.environ.get("SIMULATION_MODE", "true").lower() != "false"
# Confirmation manuelle avant chaque clic réel dans Conqueror. Désactivée par
# défaut depuis validation du parcours Sple Partie -> Nbre joueurs -> OK.
# Remettre à "true" (CONFIRMATION_MANUELLE=true) pour tout nouveau parcours
# pas encore validé, ou avant un vrai passage en service (cf. CDC 2.4).
CONFIRMATION_MANUELLE = os.environ.get("CONFIRMATION_MANUELLE", "false").lower() != "false"
HEARTBEAT_INTERVAL_S = 3

sio = socketio.Client()


# --------------------------------------------------------------------------
# Intégration Conqueror (pywinauto) - seulement chargée si mode réel
# --------------------------------------------------------------------------
def _cliquer(controle, pause_s: float = 0.4):
    """
    Clic robuste : essaie invoke() (appel direct via l'API d'accessibilité
    Windows, indépendant des coordonnées écran / de la fenêtre au premier
    plan) puis se rabat sur click_input() (clic souris réel) si le contrôle
    ne supporte pas l'InvokePattern (ex: labels texte cliquables).

    Sans confirmation manuelle entre chaque étape, click_input() seul s'est
    montré peu fiable sur les boutons WPF custom de Conqueror (clic "perdu",
    sans effet, sans erreur levée) -> invoke() + pause après coup.
    """
    try:
        controle.invoke()
    except Exception:
        controle.click_input()
    time.sleep(pause_s)


# --------------------------------------------------------------------------
def ouvrir_nouvelle_partie_reelle(data: dict) -> dict:
    """
    Pilote réellement Conqueror via pywinauto.
    Parcours relevé le 2026-07-18 via bot/inspect_conqueror.py sur la version
    'QubicaAMF Conqueror X - 14.97.01' (à revalider si Conqueror est mis à
    jour, cf. CDC 2.4) :

      1. Écran "Liste d'attente" : saisie référence + clic "Sple Partie"
         (ouvre la piste -> écran "LaneControl").
      2. Écran "LaneControl" : clic "Nbre joueurs" (ouvre le dialogue "dlg").
      3. Dialogue "Nombre de joueurs" : boutons 0 à 12 (un bouton = un total
         de joueurs, pas une saisie chiffre par chiffre), puis "OK".
      4. Pour chaque joueur (data["joueurs"]) : clic sur son nom par défaut
         ("joueur1", "joueur2"...) -> dialogue "Modifier les options du
         joueur..." -> saisie nom réel (+ pointure/bumpers si fournis) -> OK.

    Chaque étape a sa propre confirmation manuelle (système en production),
    activable via CONFIRMATION_MANUELLE=true.

    Sélection de la piste (RessourceCombobox) toujours pas automatisée :
    la piste actuellement sélectionnée par défaut dans Conqueror est utilisée.
    """
    from pywinauto import Application  # import local : uniquement nécessaire en mode réel

    app = Application(backend="uia").connect(title_re=".*Conqueror.*")
    fenetre = app.top_window()

    # Sans confirmation manuelle, rien ne ramène plus Conqueror au premier
    # plan entre les étapes (avant, taper "o" dans le terminal le faisait
    # indirectement) -> on le fait explicitement, sinon les clics partent
    # dans le vide si une autre fenêtre (terminal, VS Code...) est active.
    fenetre.set_focus()
    time.sleep(0.3)

    nom = data.get("nom", "Test")
    nb_joueurs = str(data.get("nbJoueurs", 1))

    # --- Étape 1/3 : référence + "Sple Partie" ---
    champ_reference = fenetre.child_window(auto_id="RéférenceEntry", control_type="Edit")
    champ_reference.set_text(nom)
    print(f"[bot] Champ Référence rempli avec {nom!r}.")

    # Note : "Sple Partie", "Dble Partie", "Sple Temps", "Dble Temps", "Retire"
    # partagent tous le même auto_id générique ('btn') dans Conqueror -> on cible
    # par titre visible, pas par auto_id, pour ce bouton précis.
    bouton_sple_partie = fenetre.child_window(title="Sple Partie", control_type="Button")

    if CONFIRMATION_MANUELLE:
        reponse = input(
            f"[bot] Étape 1/3 : cliquer 'Sple Partie' avec la référence {nom!r}. Confirmer ? (o/N) : "
        ).strip().lower()
        if reponse != "o":
            print("[bot] Annulé à l'étape 1 : aucun clic effectué.")
            return {"succes": False, "erreur": "annule_etape_sple_partie"}

    _cliquer(bouton_sple_partie)
    print("[bot] Clic 'Sple Partie' effectué.")

    # --- Étape 2/3 : "Nbre joueurs" (attend la transition vers LaneControl) ---
    bouton_nb_joueurs = fenetre.child_window(auto_id="btnNbre joueurs", control_type="Button")
    bouton_nb_joueurs.wait("visible enabled", timeout=10)

    if CONFIRMATION_MANUELLE:
        reponse2 = input("[bot] Étape 2/3 : cliquer 'Nbre joueurs'. Confirmer ? (o/N) : ").strip().lower()
        if reponse2 != "o":
            print("[bot] Annulé à l'étape 2 : piste ouverte, joueurs non configurés.")
            return {"succes": True, "piste": data.get("piste"), "nomJoueur": nom, "etape": "arrete_avant_nb_joueurs"}

    _cliquer(bouton_nb_joueurs)
    print("[bot] Clic 'Nbre joueurs' effectué.")

    # --- Étape 3/3 : dialogue "Nombre de joueurs" (boutons 0-12 + OK) ---
    # Les auto_id des boutons numériques sont des identifiants techniques
    # volatils (changent à chaque session Conqueror) -> ciblage par texte
    # visible ("1", "2"...), stable.
    dialogue = fenetre.child_window(auto_id="dlg", control_type="Window")
    dialogue.wait("visible enabled", timeout=10)

    bouton_valeur = dialogue.child_window(title=nb_joueurs, control_type="Button")

    if CONFIRMATION_MANUELLE:
        reponse3 = input(
            f"[bot] Étape 3/3 : sélectionner {nb_joueurs} joueur(s) puis OK. Confirmer ? (o/N) : "
        ).strip().lower()
        if reponse3 != "o":
            print("[bot] Annulé à l'étape 3 : nombre de joueurs non validé.")
            return {
                "succes": True,
                "piste": data.get("piste"),
                "nomJoueur": nom,
                "etape": "arrete_avant_validation_joueurs",
            }

    _cliquer(bouton_valeur)
    _cliquer(dialogue.child_window(auto_id="btnOK", control_type="Button"))
    print(f"[bot] {nb_joueurs} joueur(s) validé(s).")

    # --- Étape 4/4 : renommage des joueurs (optionnel, selon data["joueurs"]) ---
    joueurs = data.get("joueurs") or []
    noms_appliques = []

    if joueurs:
        if CONFIRMATION_MANUELLE:
            reponse4 = input(
                f"[bot] Étape 4/4 : configurer {len(joueurs)} joueur(s) "
                f"({', '.join(j.get('nom', '?') for j in joueurs)}). Confirmer ? (o/N) : "
            ).strip().lower()
            if reponse4 != "o":
                print("[bot] Annulé à l'étape 4 : joueurs laissés avec leur nom par défaut.")
                joueurs = []

        for index, info_joueur in enumerate(joueurs, start=1):
            if index > int(nb_joueurs):
                break  # sécurité : ne pas dépasser le nombre de joueurs réellement créés

            nom_joueur = info_joueur.get("nom")
            if not nom_joueur:
                continue

            nom_defaut = f"joueur{index}"
            try:
                _cliquer(fenetre.child_window(title=nom_defaut, control_type="Text"))
            except Exception as exc:
                print(f"[bot] Impossible de cliquer sur {nom_defaut!r} : {exc}")
                continue

            dialogue_joueur = fenetre.child_window(
                title_re="Modifier les options du joueur.*", control_type="Window"
            )
            dialogue_joueur.wait("visible enabled", timeout=10)

            champ_nom = dialogue_joueur.child_window(
                auto_id="Nom (ou ID membre)Entry", control_type="Edit"
            )
            champ_nom.set_text(nom_joueur)

            pointure = info_joueur.get("pointure")
            if pointure:
                champ_pointure = dialogue_joueur.child_window(auto_id="PointureEntry", control_type="Edit")
                champ_pointure.set_text(str(pointure))

            if info_joueur.get("bumpers"):
                case_bumpers = dialogue_joueur.child_window(auto_id="BumpersCheckBox", control_type="CheckBox")
                if not case_bumpers.get_toggle_state():
                    _cliquer(case_bumpers)

            _cliquer(dialogue_joueur.child_window(auto_id="btnOK", control_type="Button"))
            print(f"[bot] Joueur {index} renommé en {nom_joueur!r}.")
            noms_appliques.append(nom_joueur)

    return {
        "succes": True,
        "piste": data.get("piste"),
        "nomJoueur": nom,
        "nbJoueurs": nb_joueurs,
        "joueurs": noms_appliques,
    }


def ouvrir_nouvelle_partie_simulee(data: dict) -> dict:
    joueurs = [j.get("nom") for j in data.get("joueurs", []) if j.get("nom")]
    print(
        f"[SIMULATION] Ouverture piste + saisie nom '{data.get('nom')}' "
        f"+ joueurs {joueurs} (aucune action réelle sur Conqueror)"
    )
    time.sleep(0.5)
    return {"succes": True, "piste": 3, "nomJoueur": data.get("nom"), "joueurs": joueurs, "simule": True}


def executer_commande(data: dict) -> dict:
    try:
        if SIMULATION_MODE:
            return ouvrir_nouvelle_partie_simulee(data)
        return ouvrir_nouvelle_partie_reelle(data)
    except Exception as exc:  # noqa: BLE001 - on veut capturer tout échec pywinauto
        print(f"[ERREUR] Échec de la commande : {exc}")
        return {"succes": False, "erreur": str(exc)}


# --------------------------------------------------------------------------
# Client WebSocket
# --------------------------------------------------------------------------
def envoyer_heartbeat():
    while True:
        if sio.connected:
            sio.emit("bot_heartbeat")
        time.sleep(HEARTBEAT_INTERVAL_S)


@sio.event
def connect():
    print(f"[bot] connecté à {SERVEUR_URL} (mode {'SIMULATION' if SIMULATION_MODE else 'REEL'})")
    sio.emit("bot_register")


@sio.event
def disconnect():
    print("[bot] déconnecté du serveur")


@sio.on("executer_nouvelle_partie")
def on_executer_nouvelle_partie(data):
    print(f"[bot] commande reçue : {data}")
    resultat = executer_commande(data)
    print(f"[bot] résultat : {resultat}")
    return resultat  # acquittement renvoyé automatiquement par socketio (ack)


if __name__ == "__main__":
    print(f"Démarrage du bot Conqueror - mode {'SIMULATION' if SIMULATION_MODE else 'REEL'}")
    if not SIMULATION_MODE:
        print("ATTENTION : mode réel actif, le bot va interagir directement avec Conqueror.")

    threading.Thread(target=envoyer_heartbeat, daemon=True).start()

    sio.connect(SERVEUR_URL)
    sio.wait()
