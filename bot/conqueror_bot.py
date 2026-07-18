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
# Mode réel par défaut (interagit vraiment avec Conqueror). Remettre à "true"
# (SIMULATION_MODE=true) pour tester le canal borne<->bot sans toucher à
# Conqueror, par exemple après une mise à jour de Conqueror ou du parcours.
SIMULATION_MODE = os.environ.get("SIMULATION_MODE", "false").lower() != "false"
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
def _cliquer(controle, pause_avant_s: float = 0.3, pause_apres_s: float = 0.5):
    """
    Clic souris réel (click_input) avec pause avant/après, pour laisser le
    temps à Conqueror de finir de rendre l'écran avant le clic, et de
    traiter l'action avant l'étape suivante.

    Note : invoke() (API d'accessibilité, sans clic souris réel) a été
    essayé mais semble ne rien déclencher sur les boutons WPF custom de
    Conqueror (pas d'erreur, mais aucun effet) -> retour à click_input().
    """
    time.sleep(pause_avant_s)
    controle.click_input()
    time.sleep(pause_apres_s)


def _echapper_touches(texte: str) -> str:
    """
    Échappe les caractères spéciaux du mini-langage SendKeys de pywinauto
    (+^%~(){}[]) pour que send_keys() les tape littéralement plutôt que de
    les interpréter comme des modificateurs/touches.
    """
    speciaux = set("+^%~(){}[]")
    return "".join(f"{{{c}}}" if c in speciaux else c for c in texte)


def _remplir_champ_au_clavier(champ, valeur):
    """
    Remplit un champ par frappe clavier réelle plutôt que par set_text()
    (API UIA programmatique) : clic dans le champ pour le focus, Ctrl+A +
    Suppr pour vider le contenu existant, puis frappe du texte. set_text()
    semble ignoré par endroits sur les champs WPF custom de Conqueror ; la
    frappe simulée passe par le même chemin qu'une saisie humaine.
    """
    from pywinauto.keyboard import send_keys

    champ.click_input()
    time.sleep(0.2)
    send_keys("^a{DEL}")
    time.sleep(0.2)
    send_keys(_echapper_touches(str(valeur)), pause=0.03, with_spaces=True)
    time.sleep(0.3)


# --------------------------------------------------------------------------
def _ajouter_joueur(fenetre, nom_joueur, pointure=None, bumpers=False):
    """
    Ajoute un joueur en tapant directement son nom sur l'écran LaneControl
    (aucun clic préalable requis : taper un caractère ouvre directement le
    dialogue "Modifier les options du joueur..." pour un nouveau joueur).
    Le premier caractère déclenche l'ouverture (frappe clavier réelle via
    send_keys, pas type_keys sur le contrôle), puis le champ nom est vidé
    et retapé au clavier avec le nom complet (voir _remplir_champ_au_clavier
    - plus fiable que set_text() sur ces contrôles).
    """
    from pywinauto.keyboard import send_keys

    fenetre.set_focus()
    time.sleep(0.2)
    send_keys(_echapper_touches(nom_joueur[0]), pause=0.05)
    time.sleep(0.6)

    dialogue_joueur = fenetre.child_window(
        title_re="Modifier les options du joueur.*", control_type="Window"
    )
    dialogue_joueur.wait("visible enabled", timeout=10)

    champ_nom = dialogue_joueur.child_window(auto_id="Nom (ou ID membre)Entry", control_type="Edit")
    _remplir_champ_au_clavier(champ_nom, nom_joueur)

    if pointure:
        champ_pointure = dialogue_joueur.child_window(auto_id="PointureEntry", control_type="Edit")
        _remplir_champ_au_clavier(champ_pointure, pointure)

    if bumpers:
        case_bumpers = dialogue_joueur.child_window(auto_id="BumpersCheckBox", control_type="CheckBox")
        if not case_bumpers.get_toggle_state():
            _cliquer(case_bumpers)

    _cliquer(dialogue_joueur.child_window(auto_id="btnOK", control_type="Button"))
    print(f"[bot] Joueur ajouté : {nom_joueur!r}.")


def ouvrir_nouvelle_partie_reelle(data: dict) -> dict:
    """
    Pilote réellement Conqueror via pywinauto.
    Parcours relevé le 2026-07-18 via bot/inspect_conqueror.py sur la version
    'QubicaAMF Conqueror X - 14.97.01' (à revalider si Conqueror est mis à
    jour, cf. CDC 2.4) :

      1. Écran "Liste d'attente" : saisie référence + clic "Sple Partie"
         (ouvre la piste -> écran "LaneControl").
      2. Pour chaque joueur (data["joueurs"]) : saisie directe du nom au
         clavier (voir _ajouter_joueur) -> dialogue "Modifier les options
         du joueur..." -> nom (+ pointure/bumpers si fournis) -> OK.
         Plus besoin du dialogue "Nbre joueurs" (0-12) : la saisie directe
         crée les joueurs un par un.
      3. Clic "Ajout parties" -> dialogue "Nombre de parties" (boutons
         0-12, mêmes propriétés que "Nbre joueurs" : le clic sur le chiffre
         valide directement, pas de bouton "OK" séparé).

    Chaque étape a sa propre confirmation manuelle (système en production),
    activable via CONFIRMATION_MANUELLE=true.

    Non gérés pour l'instant (à voir en Phase 4, cf. CDC section 3) :
    sélection de la piste (RessourceCombobox - la piste par défaut est
    utilisée), tarifs CE.
    """
    from pywinauto import Application  # import local : uniquement nécessaire en mode réel

    app = Application(backend="uia").connect(title_re=".*Conqueror.*")
    fenetre = app.top_window()

    # Sans confirmation manuelle, rien ne ramène plus Conqueror au premier
    # plan entre les étapes (avant, taper "o" dans le terminal le faisait
    # indirectement) -> on le fait explicitement, sinon les clics/frappes
    # partent dans le vide si une autre fenêtre (terminal, VS Code...) est
    # active.
    fenetre.set_focus()
    time.sleep(0.3)

    nom = data.get("nom", "Test")
    nb_parties = str(data.get("nbParties", 1))
    joueurs = data.get("joueurs") or []

    # --- Étape 1 : référence + "Sple Partie" ---
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

    # Attend la transition vers l'écran LaneControl (bouton "Ajout parties"
    # utilisé comme simple indicateur que l'écran est bien chargé).
    bouton_ajout_parties = fenetre.child_window(title="Ajout parties", control_type="Button")
    bouton_ajout_parties.wait("visible enabled", timeout=10)

    # --- Étape 2 : ajout des joueurs (saisie directe) ---
    noms_appliques = []
    if joueurs:
        if CONFIRMATION_MANUELLE:
            reponse2 = input(
                f"[bot] Étape 2/3 : ajouter {len(joueurs)} joueur(s) "
                f"({', '.join(j.get('nom', '?') for j in joueurs)}). Confirmer ? (o/N) : "
            ).strip().lower()
            if reponse2 != "o":
                print("[bot] Annulé à l'étape 2 : aucun joueur ajouté.")
                joueurs = []

        for info_joueur in joueurs:
            nom_joueur = info_joueur.get("nom")
            if not nom_joueur:
                continue
            try:
                _ajouter_joueur(
                    fenetre,
                    nom_joueur,
                    pointure=info_joueur.get("pointure"),
                    bumpers=info_joueur.get("bumpers", False),
                )
                noms_appliques.append(nom_joueur)
            except Exception as exc:
                print(f"[bot] Échec ajout joueur {nom_joueur!r} : {exc}")

    # --- Étape 3 : "Ajout parties" -> dialogue "Nombre de parties" ---
    if CONFIRMATION_MANUELLE:
        reponse3 = input(
            f"[bot] Étape 3/3 : cliquer 'Ajout parties' et sélectionner {nb_parties}. Confirmer ? (o/N) : "
        ).strip().lower()
        if reponse3 != "o":
            print("[bot] Annulé à l'étape 3 : nombre de parties non configuré.")
            return {
                "succes": True,
                "piste": data.get("piste"),
                "nomJoueur": nom,
                "joueurs": noms_appliques,
                "etape": "arrete_avant_ajout_parties",
            }

    _cliquer(bouton_ajout_parties)

    dialogue_parties = fenetre.child_window(auto_id="dlg", control_type="Window")
    dialogue_parties.wait("visible enabled", timeout=10)

    # Comme pour "Nbre joueurs" : le clic sur le chiffre valide directement,
    # pas de bouton "OK" séparé à cliquer ensuite.
    _cliquer(dialogue_parties.child_window(title=nb_parties, control_type="Button"))
    print(f"[bot] {nb_parties} partie(s) configurée(s).")

    return {
        "succes": True,
        "piste": data.get("piste"),
        "nomJoueur": nom,
        "joueurs": noms_appliques,
        "nbParties": nb_parties,
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
