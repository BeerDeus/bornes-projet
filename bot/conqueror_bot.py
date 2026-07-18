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
HEARTBEAT_INTERVAL_S = 3

sio = socketio.Client()


# --------------------------------------------------------------------------
# Intégration Conqueror (pywinauto) - seulement chargée si mode réel
# --------------------------------------------------------------------------
def ouvrir_nouvelle_partie_reelle(data: dict) -> dict:
    """
    Pilote réellement Conqueror via pywinauto.
    À adapter avec les vrais identifiants UI de Conqueror (voir CDC 2.4 :
    documenter la version logicielle + les sélecteurs utilisés).
    """
    from pywinauto import Application  # import local : uniquement nécessaire en mode réel

    # TODO: ajuster le titre exact de la fenêtre Conqueror
    app = Application(backend="uia").connect(title_re=".*Conqueror.*")
    fenetre = app.top_window()

    # TODO: remplacer par les vrais identifiants (Button, Edit...) trouvés
    # via l'inspecteur pywinauto (python -m pywinauto.actionlogger ou
    # print_control_identifiers()) sur le poste Conqueror.
    fenetre.child_window(title="Nouvelle Partie", control_type="Button").click_input()
    champ_nom = fenetre.child_window(control_type="Edit")
    champ_nom.set_text(data.get("nom", "Test"))
    fenetre.child_window(title="Valider", control_type="Button").click_input()

    return {"succes": True, "piste": None, "nomJoueur": data.get("nom")}


def ouvrir_nouvelle_partie_simulee(data: dict) -> dict:
    print(f"[SIMULATION] Ouverture piste + saisie nom '{data.get('nom')}' (aucune action réelle sur Conqueror)")
    time.sleep(0.5)
    return {"succes": True, "piste": 3, "nomJoueur": data.get("nom"), "simule": True}


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
