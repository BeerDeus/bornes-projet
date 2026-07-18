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

import ctypes
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
def _forcer_premier_plan(fenetre) -> bool:
    """
    set_focus() seul peut échouer SILENCIEUSEMENT (aucune erreur, mais rien
    ne se passe) à cause du verrou de premier plan de Windows : un processus
    en arrière-plan (ce script, lancé depuis un terminal) n'est normalement
    pas autorisé à voler le focus clavier à la fenêtre active. C'est
    cohérent avec le fait que les clics souris (click_input) fonctionnent
    -> ils ne dépendent pas du focus clavier -> alors que la frappe clavier
    simulée (send_keys) échoue silencieusement.

    Contournement classique : simuler une touche Alt juste avant
    SetForegroundWindow, ce qui satisfait la condition de Windows et
    débloque le changement de premier plan. On vérifie ensuite explicitement
    que ça a marché plutôt que de le supposer.
    """
    user32 = ctypes.windll.user32
    hwnd = fenetre.handle
    user32.keybd_event(0x12, 0, 0, 0)  # Alt down
    user32.keybd_event(0x12, 0, 0x0002, 0)  # Alt up
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    reussi = user32.GetForegroundWindow() == hwnd
    print(f"[bot] Conqueror au premier plan : {'OK' if reussi else 'ÉCHEC'}")
    return reussi


def _cliquer(controle, timeout_attente_s: float = 5, pause_apres_s: float = 0.1):
    """
    Attend que le contrôle soit prêt (vérifié environ toutes les 0,1s) et
    clique dès qu'il est détecté, au lieu d'une pause fixe avant le clic
    -> plus rapide quand Conqueror répond vite, toujours robuste quand il
    est plus lent. Petite pause après le clic pour laisser le temps de
    traiter l'action avant l'étape suivante.

    Note : invoke() (API d'accessibilité, sans clic souris réel) a été
    essayé mais semble ne rien déclencher sur les boutons WPF custom de
    Conqueror (pas d'erreur, mais aucun effet) -> retour à click_input().
    """
    controle.wait("visible enabled", timeout=timeout_attente_s, retry_interval=0.1)
    controle.click_input()
    time.sleep(pause_apres_s)


# --------------------------------------------------------------------------
def _configurer_joueur(fenetre, nom_defaut, nom_joueur, bumpers=False):
    """
    Renomme/configure un joueur existant (placeholder "joueurN" créé par le
    dialogue "Nbre joueurs") : clic sur son nom par défaut (souris, fiable)
    -> dialogue "Modifier les options du joueur..." -> remplissage des
    champs via set_text() (API d'accessibilité UIA, PAS une frappe clavier
    simulée) -> OK.

    Important : Conqueror semble ignorer les frappes clavier injectées
    (send_keys/type_keys), probablement un filtre anti-injection courant
    sur les logiciels de caisse qui gèrent aussi des douchettes code-barres
    en mode clavier. set_text() contourne le problème car il ne simule pas
    d'évènement clavier : il écrit la valeur directement via le fournisseur
    d'accessibilité de l'élément.
    """
    _cliquer(fenetre.child_window(title=nom_defaut, control_type="Text"))

    dialogue_joueur = fenetre.child_window(
        title_re="Modifier les options du joueur.*", control_type="Window"
    )
    dialogue_joueur.wait("visible enabled", timeout=10)

    champ_nom = dialogue_joueur.child_window(auto_id="Nom (ou ID membre)Entry", control_type="Edit")
    champ_nom.set_text(nom_joueur)

    if bumpers:
        case_bumpers = dialogue_joueur.child_window(auto_id="BumpersCheckBox", control_type="CheckBox")
        if not case_bumpers.get_toggle_state():
            _cliquer(case_bumpers)

    _cliquer(dialogue_joueur.child_window(auto_id="btnOK", control_type="Button"))
    print(f"[bot] Joueur {nom_defaut!r} renommé en {nom_joueur!r}.")


def _appliquer_tarif_ce(fenetre, nom_joueur):
    """
    Applique le tarif "CE" (Pass CE) à un seul joueur, sur l'écran
    LaneControl :
      1. Décoche la case "sélectionné" de tous les joueurs de la piste.
      2. Coche uniquement celle du joueur concerné.
      3. Clique "Tarifs" -> dialogue "Tarif par défaut..." -> clique "CE".

    Repérage de la case à cocher : les cases n'ont ni texte ni auto_id
    stable (identifiants techniques volatils, comme les boutons numériques
    des dialogues 0-12). Sur la structure observée le 2026-07-18, chaque
    joueur occupe un bloc de 9 éléments après son nom (3 cases, 3 textes de
    statut/parties/totaux, 2 totaux, puis la case "sélectionné" en dernière
    position, juste avant le nom du joueur suivant) -> on la retrouve par
    position relative au Text du nom. Fragile si Conqueror change cette
    disposition ; à revalider si ça ne fonctionne plus après une mise à
    jour (cf. CDC 2.4).
    """
    DECALAGE_CASE_SELECTION = 9

    lane_control = fenetre.child_window(auto_id="LaneControl", control_type="Window")
    enfants = lane_control.children()

    # 1. Décoche toutes les cases à cocher de l'écran (piste + joueurs).
    for enfant in enfants:
        try:
            if enfant.friendly_class_name() != "CheckBox":
                continue
            if enfant.get_toggle_state():
                enfant.click_input()
                time.sleep(0.05)
        except Exception:
            continue

    # 2. Repère le nom du joueur, prend la case 9 positions plus loin.
    index_nom = None
    for i, enfant in enumerate(enfants):
        try:
            if enfant.friendly_class_name() == "Text" and enfant.window_text() == nom_joueur:
                index_nom = i
                break
        except Exception:
            continue

    if index_nom is None or index_nom + DECALAGE_CASE_SELECTION >= len(enfants):
        raise RuntimeError(f"Case à cocher du joueur {nom_joueur!r} introuvable (structure inattendue)")

    case_joueur = enfants[index_nom + DECALAGE_CASE_SELECTION]
    if case_joueur.friendly_class_name() != "CheckBox":
        raise RuntimeError(
            f"Élément inattendu à la position 'case sélectionnée' du joueur {nom_joueur!r} : "
            f"{case_joueur.friendly_class_name()} (structure Conqueror probablement différente)"
        )

    case_joueur.click_input()
    time.sleep(0.1)

    # 3. "Tarifs" -> dialogue "Tarif par défaut..." -> "CE"
    _cliquer(fenetre.child_window(auto_id="btnTarifs", control_type="Button"))
    dialogue_tarif = fenetre.child_window(auto_id="DlgSelectPrice", control_type="Window")
    _cliquer(dialogue_tarif.child_window(title="CE", control_type="Button"))
    print(f"[bot] Tarif CE appliqué à {nom_joueur!r}.")


def ouvrir_nouvelle_partie_reelle(data: dict) -> dict:
    """
    Pilote réellement Conqueror via pywinauto.
    Parcours relevé le 2026-07-18 via bot/inspect_conqueror.py sur la version
    'QubicaAMF Conqueror X - 14.97.01' (à revalider si Conqueror est mis à
    jour, cf. CDC 2.4) :

      1. Écran "Liste d'attente" : saisie référence + clic "Sple Partie"
         (ouvre la piste -> écran "LaneControl").
      2. Clic "Nbre joueurs" -> dialogue "dlg" -> clic sur le chiffre
         (validation directe, pas de bouton "OK" séparé) -> crée N
         placeholders "joueur1".."joueurN".
      3. Pour chaque joueur (data["joueurs"]) : clic sur son placeholder
         ("joueur1", "joueur2"...) -> dialogue "Modifier les options du
         joueur..." -> nom (+ bumpers si fourni, via set_text(), PAS de
         frappe clavier simulée) -> OK. Voir _configurer_joueur. Si le
         joueur a "passCE": true, applique en plus le tarif CE (voir
         _appliquer_tarif_ce : décoche tout, coche ce joueur, Tarifs, CE).
      4. Clic "Ajout parties" -> dialogue "Nombre de parties" (même
         comportement que "Nbre joueurs" : clic chiffre = validation
         directe).

    Note importante (2026-07-18) : Conqueror semble ignorer les frappes
    clavier synthétiques (send_keys/type_keys), même une fois la fenêtre
    correctement passée au premier plan — probablement un filtre
    anti-injection courant sur les logiciels de caisse (protection contre
    les fausses douchettes code-barres en mode clavier). D'où l'usage
    systématique de clics souris (click_input, fiable) et de set_text()
    (API d'accessibilité, pas un évènement clavier) plutôt que de toute
    forme de frappe simulée.

    Chaque étape a sa propre confirmation manuelle (système en production),
    activable via CONFIRMATION_MANUELLE=true.

    Non géré pour l'instant (à voir en Phase 4, cf. CDC section 3) :
    sélection de la piste (RessourceCombobox - la piste par défaut est
    utilisée).
    """
    from pywinauto import Application  # import local : uniquement nécessaire en mode réel

    app = Application(backend="uia").connect(title_re=".*Conqueror.*")
    fenetre = app.top_window()

    # Sans confirmation manuelle, rien ne ramène plus Conqueror au premier
    # plan entre les étapes (avant, taper "o" dans le terminal le faisait
    # indirectement) -> on le fait explicitement, sinon les clics/frappes
    # partent dans le vide si une autre fenêtre (terminal, VS Code...) est
    # active.
    _forcer_premier_plan(fenetre)

    nom = data.get("nom", "Test")
    joueurs = data.get("joueurs") or []
    nb_joueurs = str(len(joueurs) or data.get("nbJoueurs", 1))
    nb_parties = str(data.get("nbParties", 1))

    # --- Étape 1/4 : référence + "Sple Partie" ---
    champ_reference = fenetre.child_window(auto_id="RéférenceEntry", control_type="Edit")
    champ_reference.set_text(nom)
    print(f"[bot] Champ Référence rempli avec {nom!r}.")

    # Note : "Sple Partie", "Dble Partie", "Sple Temps", "Dble Temps", "Retire"
    # partagent tous le même auto_id générique ('btn') dans Conqueror -> on cible
    # par titre visible, pas par auto_id, pour ce bouton précis.
    bouton_sple_partie = fenetre.child_window(title="Sple Partie", control_type="Button")

    if CONFIRMATION_MANUELLE:
        reponse = input(
            f"[bot] Étape 1/4 : cliquer 'Sple Partie' avec la référence {nom!r}. Confirmer ? (o/N) : "
        ).strip().lower()
        if reponse != "o":
            print("[bot] Annulé à l'étape 1 : aucun clic effectué.")
            return {"succes": False, "erreur": "annule_etape_sple_partie"}

    _cliquer(bouton_sple_partie)
    print("[bot] Clic 'Sple Partie' effectué.")

    # bouton_nb_joueurs : _cliquer() attendra lui-même la transition vers
    # l'écran LaneControl (polling ~0,1s) avant de cliquer.
    bouton_nb_joueurs = fenetre.child_window(auto_id="btnNbre joueurs", control_type="Button")

    # --- Étape 2/4 : "Nbre joueurs" -> dialogue "dlg" (validation directe) ---
    if CONFIRMATION_MANUELLE:
        reponse2 = input(
            f"[bot] Étape 2/4 : cliquer 'Nbre joueurs' et sélectionner {nb_joueurs}. Confirmer ? (o/N) : "
        ).strip().lower()
        if reponse2 != "o":
            print("[bot] Annulé à l'étape 2 : piste ouverte, joueurs non configurés.")
            return {"succes": True, "piste": data.get("piste"), "nomJoueur": nom, "etape": "arrete_avant_nb_joueurs"}

    _cliquer(bouton_nb_joueurs)

    dialogue_nb = fenetre.child_window(auto_id="dlg", control_type="Window")
    _cliquer(dialogue_nb.child_window(title=nb_joueurs, control_type="Button"))
    print(f"[bot] {nb_joueurs} joueur(s) créé(s) (placeholders).")

    # --- Étape 3/4 : configuration de chaque joueur (clic + set_text) ---
    noms_appliques = []
    if joueurs:
        if CONFIRMATION_MANUELLE:
            reponse3 = input(
                f"[bot] Étape 3/4 : configurer {len(joueurs)} joueur(s) "
                f"({', '.join(j.get('nom', '?') for j in joueurs)}). Confirmer ? (o/N) : "
            ).strip().lower()
            if reponse3 != "o":
                print("[bot] Annulé à l'étape 3 : joueurs laissés avec leur nom par défaut.")
                joueurs = []

        for index, info_joueur in enumerate(joueurs, start=1):
            nom_joueur = info_joueur.get("nom")
            if not nom_joueur:
                continue
            try:
                _configurer_joueur(
                    fenetre,
                    f"joueur{index}",
                    nom_joueur,
                    bumpers=info_joueur.get("bumpers", False),
                )
                noms_appliques.append(nom_joueur)

                if info_joueur.get("passCE"):
                    try:
                        _appliquer_tarif_ce(fenetre, nom_joueur)
                    except Exception as exc:
                        print(f"[bot] Échec application tarif CE pour {nom_joueur!r} : {exc}")
            except Exception as exc:
                print(f"[bot] Échec configuration joueur {nom_joueur!r} : {exc}")

    # --- Étape 4/4 : "Ajout parties" -> dialogue "Nombre de parties" ---
    bouton_ajout_parties = fenetre.child_window(title="Ajout parties", control_type="Button")

    if CONFIRMATION_MANUELLE:
        reponse4 = input(
            f"[bot] Étape 4/4 : cliquer 'Ajout parties' et sélectionner {nb_parties}. Confirmer ? (o/N) : "
        ).strip().lower()
        if reponse4 != "o":
            print("[bot] Annulé à l'étape 4 : nombre de parties non configuré.")
            return {
                "succes": True,
                "piste": data.get("piste"),
                "nomJoueur": nom,
                "joueurs": noms_appliques,
                "etape": "arrete_avant_ajout_parties",
            }

    _cliquer(bouton_ajout_parties)

    dialogue_parties = fenetre.child_window(auto_id="dlg", control_type="Window")
    _cliquer(dialogue_parties.child_window(title=nb_parties, control_type="Button"))
    print(f"[bot] {nb_parties} partie(s) configurée(s).")

    return {
        "succes": True,
        "piste": data.get("piste"),
        "nomJoueur": nom,
        "joueurs": noms_appliques,
        "nbJoueurs": nb_joueurs,
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
