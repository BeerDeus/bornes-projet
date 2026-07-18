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
# Tant que le mode réel n'a pas été validé plusieurs fois sans souci, on garde
# une confirmation manuelle obligatoire avant tout clic réel dans Conqueror
# (le bot est connecté au système de PRODUCTION, pas un environnement de test).
CONFIRMATION_MANUELLE = os.environ.get("CONFIRMATION_MANUELLE", "true").lower() != "false"
HEARTBEAT_INTERVAL_S = 3

sio = socketio.Client()


# --------------------------------------------------------------------------
# Intégration Conqueror (pywinauto) - seulement chargée si mode réel
# --------------------------------------------------------------------------
def ouvrir_nouvelle_partie_reelle(data: dict) -> dict:
    """
    Pilote réellement Conqueror via pywinauto.
    Identifiants relevés le 2026-07-18 via bot/inspect_conqueror.py sur la
    version 'QubicaAMF Conqueror X - 14.97.01' (écran Liste d'attente /
    WaitingList). À revalider si Conqueror est mis à jour (cf. CDC 2.4).

    Sélection de la piste (RessourceCombobox) volontairement pas encore
    automatisée : comportement du combo (saisie directe vs liste déroulante)
    pas encore confirmé en conditions réelles. Le bouton "Sple Partie" (partie
    simple) utilisera donc la ressource actuellement sélectionnée par défaut
    dans Conqueror, jusqu'à ce qu'on valide et ajoute la sélection automatique.
    """
    from pywinauto import Application  # import local : uniquement nécessaire en mode réel

    app = Application(backend="uia").connect(title_re=".*Conqueror.*")
    fenetre = app.top_window()

    champ_reference = fenetre.child_window(auto_id="RéférenceEntry", control_type="Edit")
    nom = data.get("nom", "Test")
    champ_reference.set_text(nom)
    print(f"[bot] Champ Référence rempli avec {nom!r} (rien envoyé à Conqueror pour l'instant).")

    # TODO (prochaine itération) : sélectionner la piste via
    # fenetre.child_window(auto_id="RessourceCombobox", control_type="ComboBox")
    # une fois son comportement confirmé.

    # Note : "Sple Partie", "Dble Partie", "Sple Temps", "Dble Temps", "Retire"
    # partagent tous le même auto_id générique ('btn') dans Conqueror -> on cible
    # par titre visible, pas par auto_id, pour ce bouton précis.
    bouton_action = fenetre.child_window(title="Sple Partie", control_type="Button")

    if CONFIRMATION_MANUELLE:
        reponse = input(
            "[bot] Prêt à cliquer sur 'Sple Partie' dans Conqueror avec la référence "
            f"{nom!r}. Confirmer ? (o/N) : "
        ).strip().lower()
        if reponse != "o":
            print("[bot] Annulé : aucun clic effectué dans Conqueror.")
            return {"succes": False, "erreur": "annule_par_confirmation_manuelle"}

    bouton_action.click_input()
    print("[bot] Clic sur 'Sple Partie' effectué.")

    return {"succes": True, "piste": data.get("piste"), "nomJoueur": nom}


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
