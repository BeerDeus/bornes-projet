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

DOSSIER_SCANS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scans")


# --------------------------------------------------------------------------
# Diagnostic - scan automatique de l'écran au moment d'un échec
# --------------------------------------------------------------------------
def _dump_controle(controle, depth=0, lignes=None, max_profondeur=8, max_elements=800):
    """
    Réplique la logique de dump() de inspect_conqueror.py, réutilisable
    depuis le bot lui-même : sert à générer un scan automatique de l'écran
    au moment précis d'un échec, sans avoir à relancer inspect_conqueror.py
    à la main après coup (l'état a pu avoir changé entre-temps, ex: retour à
    un autre écran après l'erreur).
    """
    if lignes is None:
        lignes = []
    if len(lignes) >= max_elements or depth > max_profondeur:
        return lignes
    try:
        texte = controle.window_text()
    except Exception:
        texte = ""
    try:
        control_type = controle.element_info.control_type
    except Exception:
        try:
            control_type = controle.friendly_class_name()
        except Exception:
            control_type = "?"
    try:
        auto_id = controle.element_info.automation_id
    except Exception:
        auto_id = ""
    lignes.append("  " * depth + f"- [{control_type}] texte={texte!r} auto_id={auto_id!r}")
    try:
        enfants = controle.children()
    except Exception as exc:
        lignes.append("  " * (depth + 1) + f"(erreur lecture des enfants: {exc})")
        return lignes
    for enfant in enfants:
        if len(lignes) >= max_elements:
            break
        _dump_controle(enfant, depth + 1, lignes, max_profondeur, max_elements)
    return lignes


def _scan_diagnostic(controle, prefixe_nom_fichier: str) -> str:
    """
    Écrit un scan de `controle` (et ses enfants) dans bot/scans/, avec un nom
    horodaté, façon inspect_conqueror.py - mais déclenché automatiquement par
    le bot lui-même au moment exact d'un échec, ce qui est plus fiable qu'un
    scan manuel après coup (l'écran a pu déjà changer, ex: message d'erreur
    Conqueror affiché entre-temps). Best-effort : une erreur ici ne doit
    jamais faire planter le bot / la commande en cours.
    """
    try:
        os.makedirs(DOSSIER_SCANS, exist_ok=True)
        horodatage = time.strftime("%Y%m%d_%H%M%S")
        chemin = os.path.join(DOSSIER_SCANS, f"{prefixe_nom_fichier}_{horodatage}.txt")
        lignes = _dump_controle(controle)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write("\n".join(lignes))
        print(f"[bot][debug] Scan diagnostic écrit ({len(lignes)} éléments) : {chemin}")
        return chemin
    except Exception as exc:
        print(f"[bot][debug] Échec écriture scan diagnostic : {exc}")
        return ""


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


def _cliquer(controle, timeout_attente_s: float = 5, pause_apres_s: float = 0.03):
    """
    Attend que le contrôle soit prêt (vérifié environ toutes les 0,03s) et
    clique dès qu'il est détecté, au lieu d'une pause fixe avant le clic
    -> plus rapide quand Conqueror répond vite, toujours robuste quand il
    est plus lent. Petite pause après le clic pour laisser le temps de
    traiter l'action avant l'étape suivante.

    Note : invoke() (API d'accessibilité, sans clic souris réel) a été
    essayé mais semble ne rien déclencher sur les boutons WPF custom de
    Conqueror (pas d'erreur, mais aucun effet) -> retour à click_input().

    Constantes resserrées le 2026-07-19 (0.1s -> 0.03s) pour accélérer le
    parcours : le polling par .wait() ne bloque déjà que le temps
    nécessaire, donc réduire son intervalle et la pause post-clic gagne du
    temps sans rien retirer côté fiabilité (cf. CDC 2.4). Si des échecs
    intermittents réapparaissent après ce changement, remonter d'abord
    pause_apres_s avant de suspecter la structure Conqueror.
    """
    controle.wait("visible enabled", timeout=timeout_attente_s, retry_interval=0.03)
    controle.click_input()
    time.sleep(pause_apres_s)


TAILLE_BLOC_JOUEUR = 10


def _reperer_bloc_joueur(fenetre, index_joueur):
    """
    Retourne (lane_control, enfants, index_nom) : la liste FRAÎCHE des
    enfants de LaneControl et l'index du Text nom du joueur #index_joueur
    (1-based, ordre de création), repéré par POSITION plutôt que par
    recherche de titre.

    Historique : la recherche par titre (fenetre/lane_control.child_window
    (title=nom_defaut, control_type="Text")) a échoué le 2026-07-19 pour le
    2e joueur ('Bob') avec "There are 2 elements that match the criteria"
    -> DEUX Text 'joueur2' existaient simultanément au moment de la
    recherche, y compris en scopant déjà la recherche à LaneControl (donc
    pas un résidu d'une autre fenêtre comme d'abord supposé). Hypothèse la
    plus probable : Conqueror régénère les conteneurs de la liste de
    joueurs (WPF ItemsControl) après une vente complète (transaction PDV du
    1er joueur), ce qui peut exposer transitoirement l'ancien ET le nouveau
    conteneur du 2e joueur à UIA, même sans qu'il ait lui-même été modifié.
    Une recherche par titre est vulnérable à ce doublon transitoire ; un
    index calculé sur un SEUL scan de enfants ne l'est pas (on prend
    l'élément à une position, peu importe qu'il y en ait un autre ailleurs
    dans la liste avec le même texte).

    Repérage validé sur tous les scans collectés (2 et 7 joueurs, avant/
    après renommage, décoché) : le 1er joueur commence toujours
    immédiatement après le bouton "Enregistrer", chaque joueur suivant
    occupe un bloc fixe de TAILLE_BLOC_JOUEUR éléments. À revalider si
    Conqueror change cette disposition (cf. CDC 2.4).

    Bug 2026-07-19 (régression) : appelé pour le 1er joueur ('Alice') juste
    après la création des placeholders (clic du chiffre dans le dialogue
    "Nbre joueurs"), échoue immédiatement avec un total de 65 éléments
    (le compte normal) mais un élément différent de "Text" à la position
    calculée. L'ancienne méthode par recherche de titre utilisait
    _cliquer(), qui attend via .wait("visible enabled", ...) que l'élément
    soit prêt -> ça absorbait implicitement un léger délai de rendu de
    Conqueror juste après la création des lignes joueurs. Le repérage
    positionnel, en un seul scan sans attente, n'a plus ce filet de
    sécurité -> ajout d'un court polling (re-scan frais à chaque tentative)
    pour retrouver cette tolérance, sans réintroduire de recherche par nom
    (donc toujours pas vulnérable au bug du doublon transitoire ci-dessus).
    """
    ATTENTE_STRUCTURE_MAX_S = 2.0
    ATTENTE_STRUCTURE_INTERVALLE_S = 0.05

    lane_control = fenetre.child_window(auto_id="LaneControl", control_type="Window")

    derniere_erreur = None
    debut = time.monotonic()
    tentatives = 0
    while True:
        tentatives += 1
        enfants = lane_control.children()

        index_enregistrer = None
        for i, enfant in enumerate(enfants):
            try:
                if enfant.friendly_class_name() == "Button" and enfant.window_text() == "Enregistrer":
                    index_enregistrer = i
                    break
            except Exception:
                continue

        if index_enregistrer is None:
            derniere_erreur = "Bouton 'Enregistrer' introuvable sur LaneControl (repère de position perdu)"
        else:
            index_nom = index_enregistrer + 1 + (index_joueur - 1) * TAILLE_BLOC_JOUEUR
            if index_nom < len(enfants) and enfants[index_nom].friendly_class_name() == "Text":
                if tentatives > 1:
                    print(f"[bot][debug] _reperer_bloc_joueur #{index_joueur} : OK après {tentatives} tentative(s).")
                return lane_control, enfants, index_nom
            derniere_erreur = (
                f"Bloc du joueur #{index_joueur} introuvable à la position calculée {index_nom} "
                f"(structure inattendue, total {len(enfants)} élément(s))"
            )

        if time.monotonic() - debut >= ATTENTE_STRUCTURE_MAX_S:
            print(f"[bot][debug] _reperer_bloc_joueur #{index_joueur} : échec après {tentatives} tentative(s).")
            raise RuntimeError(derniere_erreur)

        time.sleep(ATTENTE_STRUCTURE_INTERVALLE_S)


# --------------------------------------------------------------------------
def _configurer_joueur(fenetre, index_joueur, nom_defaut, nom_joueur, bumpers=False):
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

    Bug 2026-07-19 (2e joueur, 'Bob') : "There are 2 elements that match the
    criteria {'title': 'joueur2', ...}", persistant même en scopant la
    recherche à LaneControl (donc pas un résidu d'une autre fenêtre comme
    d'abord supposé) -> repérage par TITRE remplacé par le repérage
    POSITIONNEL de _reperer_bloc_joueur (même méthode que
    _appliquer_tarif_parties), qui ne fait plus aucune recherche par nom et
    n'est donc plus vulnérable à un doublon transitoire de conteneur. Voir
    la docstring de _reperer_bloc_joueur pour le détail.

    Chronométré en debug (clic, ouverture dialogue, écriture, clic OK,
    fermeture) pour objectiver le ressenti de lenteur signalé par Beer -
    permet de voir si le temps vient de nos attentes (contrôlables) ou du
    traitement propre à Conqueror (pas contrôlable depuis l'extérieur).
    """
    t_debut = time.monotonic()

    lane_control, enfants, index_nom = _reperer_bloc_joueur(fenetre, index_joueur)
    element_nom = enfants[index_nom]
    element_nom.click_input()
    time.sleep(0.03)
    print(f"[bot][debug] {nom_defaut!r} : clic placeholder (position {index_nom}) -> +{time.monotonic() - t_debut:.2f}s")

    dialogue_joueur = fenetre.child_window(
        title_re="Modifier les options du joueur.*", control_type="Window"
    )
    t_avant_dialogue = time.monotonic()
    dialogue_joueur.wait("visible enabled", timeout=3, retry_interval=0.02)
    print(f"[bot][debug] {nom_defaut!r} : dialogue visible -> +{time.monotonic() - t_avant_dialogue:.2f}s")

    champ_nom = dialogue_joueur.child_window(auto_id="Nom (ou ID membre)Entry", control_type="Edit")
    t_avant_ecriture = time.monotonic()
    champ_nom.set_text(nom_joueur)
    print(f"[bot][debug] {nom_defaut!r} : set_text({nom_joueur!r}) -> +{time.monotonic() - t_avant_ecriture:.2f}s")

    if bumpers:
        case_bumpers = dialogue_joueur.child_window(auto_id="BumpersCheckBox", control_type="CheckBox")
        if not case_bumpers.get_toggle_state():
            _cliquer(case_bumpers)

    t_avant_ok = time.monotonic()
    _cliquer(dialogue_joueur.child_window(auto_id="btnOK", control_type="Button"))
    print(f"[bot][debug] {nom_defaut!r} : clic OK -> +{time.monotonic() - t_avant_ok:.2f}s")

    # Attend la fermeture effective du dialogue (pas juste le clic), pour
    # être sûr que Conqueror a traité l'enregistrement avant l'étape
    # suivante.
    t_avant_fermeture = time.monotonic()
    try:
        dialogue_joueur.wait_not("visible", timeout=2, retry_interval=0.02)
        print(f"[bot][debug] {nom_defaut!r} : dialogue fermé -> +{time.monotonic() - t_avant_fermeture:.2f}s")
    except Exception as exc:
        print(f"[bot][debug] {nom_defaut!r} : dialogue TOUJOURS visible après OK ? ({exc})")

    print(f"[bot] Joueur {nom_defaut!r} renommé en {nom_joueur!r}. (cycle total : {time.monotonic() - t_debut:.2f}s)")


# Tarifs disponibles pour l'achat de parties par joueur, via
# _appliquer_tarif_parties (titres exacts des boutons dans la fenêtre PDV,
# relevés le 2026-07-19 via bot/scans/affichage_parties.txt). "1" (1 partie,
# tarif normal) est la valeur par défaut si un joueur n'a pas de "tarif"
# précisé dans la commande.
TARIFS_PARTIES = {
    "CE": "CE",
    "1": "1 partie",
    "2": "2 parties(2)",
    "3": "3 parties(3)",
    "2+1": "2+1(3)",
}


def _appliquer_tarif_parties(fenetre, index_joueur, nom_defaut, nom_joueur, tarif):
    """
    Sélectionne le tarif + nombre de parties d'UN joueur, sur l'écran
    LaneControl, en cliquant directement sur sa cellule "Parties" (colonne
    du tableau des joueurs), ce qui ouvre une fenêtre PDV dédiée
    ("PDV - Vente des parties à <nom>") où l'on choisit le tarif en un clic
    parmi les boutons TARIFS_PARTIES (CE / 1 partie / 2 parties(2) /
    3 parties(3) / 2+1(3)) puis on valide (OK / auto_id='btnPayment').

    Remplace complètement DEUX méthodes précédentes, abandonnées le
    2026-07-19 après échecs répétés malgré plusieurs corrections
    (repérage par nom du joueur puis case à cocher + bouton "Tarifs" +
    dialogue "Tarif par défaut", cf. historique git) : les scans
    auto-générés lors des échecs montraient systématiquement une structure
    correcte au moment du dump, ce qui pointait vers une fragilité propre
    à la méthode (case à cocher + dialogue de tarif global) plutôt qu'à un
    problème de timing. Cliquer directement sur "Parties" pour CE joueur,
    suggéré par Beer, élimine en plus le besoin de l'étape globale
    "Ajout parties" (qui appliquait un nombre de parties unique à tous les
    joueurs sélectionnés à la fois) : chaque joueur choisit son propre
    tarif/nombre de parties indépendamment, en un seul écran.

    Repérage de la cellule "Parties" : réutilise le repérage POSITIONNEL
    validé pour l'ancienne fonction CE (le 1er joueur commence toujours
    immédiatement après le bouton "Enregistrer", chaque joueur suivant
    occupe un bloc fixe de 10 éléments) - voir bot/scans pour les scans de
    référence. Dans ce bloc, l'ordre des colonnes (confirmé par les
    en-têtes "Tarifs" / "Parties" / "Totaux" de LaneControl) donne : nom
    +0, 3 cases +1/+2/+3, icône +4, colonne Tarifs +5, colonne PARTIES +6,
    colonne Totaux +7/+8, case "sélectionné" +9. On clique donc sur
    l'élément à l'index +6 du nom du joueur.

    ATTENTION : méthode déduite de bot/scans/affichage_parties.txt, pas
    encore validée en conditions réelles depuis cet environnement (pas
    d'accès direct à Conqueror) -> à tester en premier avec
    CONFIRMATION_MANUELLE=true ou sur un seul joueur. À revalider si
    Conqueror change cette disposition (cf. CDC 2.4).
    """
    DECALAGE_PARTIES = 6

    titre_bouton = TARIFS_PARTIES.get(tarif)
    if titre_bouton is None:
        raise RuntimeError(
            f"Tarif {tarif!r} inconnu pour {nom_joueur!r} (valeurs acceptées : {sorted(TARIFS_PARTIES)})"
        )

    print(
        f"[bot][debug] --- Parties pour {nom_joueur!r} (joueur #{index_joueur}, défaut {nom_defaut!r}) : "
        f"tarif={tarif!r} -> bouton {titre_bouton!r} ---"
    )

    try:
        lane_control, enfants, index_nom = _reperer_bloc_joueur(fenetre, index_joueur)
    except Exception:
        _scan_diagnostic(fenetre, f"auto_echec_Parties_repere_{nom_joueur}")
        raise

    index_parties = index_nom + DECALAGE_PARTIES
    print(f"[bot][debug] index_nom={index_nom} -> index_parties calculé={index_parties}.")

    if index_parties >= len(enfants):
        print(f"[bot][debug] Position calculée invalide (total {len(enfants)} élément(s)).")
        _scan_diagnostic(fenetre, f"auto_echec_Parties_{nom_joueur}")
        raise RuntimeError(f"Cellule 'Parties' du joueur {nom_joueur!r} introuvable (structure inattendue)")

    cellule_parties = enfants[index_parties]
    try:
        texte_lu = cellule_parties.window_text()
    except Exception:
        texte_lu = "?"
    print(f"[bot][debug] Cellule Parties à l'index {index_parties} : classe={cellule_parties.friendly_class_name()!r} texte={texte_lu!r}.")

    cellule_parties.click_input()
    time.sleep(0.05)

    # Ouvre la fenêtre PDV dédiée ("PDV - Vente des parties à <nom>").
    fenetre_pdv = fenetre.child_window(title_re=r"PDV - Vente des parties.*", control_type="Window")
    try:
        fenetre_pdv.wait("visible enabled", timeout=5, retry_interval=0.03)
    except Exception:
        print(f"[bot][debug] Fenêtre PDV non détectée pour {nom_joueur!r}.")
        _scan_diagnostic(fenetre, f"auto_echec_Parties_fenetrepdv_{nom_joueur}")
        raise RuntimeError(f"Fenêtre 'PDV - Vente des parties' non ouverte pour {nom_joueur!r}")

    # Vérification (non bloquante) : le titre de la fenêtre PDV doit
    # mentionner ce joueur. Sert à détecter si le clic positionnel a en
    # fait ouvert le PDV d'un AUTRE joueur (jamais vérifié jusqu'ici) -
    # piste à surveiller pour la prochaine anomalie de ce type.
    try:
        titre_pdv = fenetre_pdv.window_text()
    except Exception:
        titre_pdv = "?"
    print(f"[bot][debug] Fenêtre PDV ouverte : titre={titre_pdv!r} (attendu contenant {nom_joueur!r} ou {nom_defaut!r}).")
    if nom_joueur not in titre_pdv and nom_defaut not in titre_pdv:
        print(f"[bot][debug] ATTENTION : titre PDV ne mentionne ni {nom_joueur!r} ni {nom_defaut!r} !")

    try:
        grille_produits = fenetre_pdv.child_window(auto_id="gridProducts", control_type="Pane")
        bouton_tarif = grille_produits.child_window(title=titre_bouton, control_type="Button")
        _cliquer(bouton_tarif)

        _cliquer(fenetre_pdv.child_window(auto_id="btnPayment", control_type="Button"))

        # Vérifie la fermeture effective (plafond remonté à 4s + une
        # 2e tentative de clic OK) : une fenêtre PDV encore ouverte au
        # moment où le joueur suivant démarre peut fausser des recherches
        # ailleurs dans l'appli (cf. bug 'joueur2' ambigu du 2026-07-19,
        # cf. docstring de _configurer_joueur).
        try:
            fenetre_pdv.wait_not("visible", timeout=4, retry_interval=0.03)
        except Exception:
            print(f"[bot][debug] Fenêtre PDV de {nom_joueur!r} encore visible, nouvelle tentative de clic OK...")
            try:
                _cliquer(fenetre_pdv.child_window(auto_id="btnPayment", control_type="Button"))
                fenetre_pdv.wait_not("visible", timeout=3, retry_interval=0.03)
            except Exception as exc:
                print(f"[bot][debug] ÉCHEC fermeture fenêtre PDV de {nom_joueur!r} : {exc}")
                _scan_diagnostic(fenetre, f"auto_echec_Parties_fermeture_{nom_joueur}")

        print(f"[bot] Tarif {tarif!r} ({titre_bouton!r}) appliqué à {nom_joueur!r}.")
    except Exception:
        _scan_diagnostic(fenetre, f"auto_echec_Parties_bouton_{nom_joueur}")
        raise


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
      3. Pour chaque joueur (data["joueurs"]) :
         a. Clic sur son placeholder ("joueur1", "joueur2"...) -> dialogue
            "Modifier les options du joueur..." -> nom (+ bumpers si fourni,
            via set_text(), PAS de frappe clavier simulée) -> OK. Voir
            _configurer_joueur.
         b. Clic sur sa cellule "Parties" (colonne du tableau LaneControl)
            -> fenêtre PDV dédiée "Vente des parties à <nom>" -> clic sur
            le bouton du tarif choisi (data["joueurs"][i]["tarif"], parmi
            CE / 1 / 2 / 3 / 2+1 - "1" par défaut) -> OK. Voir
            _appliquer_tarif_parties. Remplace l'ancienne étape globale
            "Ajout parties" (retirée le 2026-07-19) : chaque joueur choisit
            désormais son propre tarif/nombre de parties indépendamment.

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

    # bouton_nb_joueurs : _cliquer() attendra lui-même la transition vers
    # l'écran LaneControl (polling ~0,1s) avant de cliquer.
    bouton_nb_joueurs = fenetre.child_window(auto_id="btnNbre joueurs", control_type="Button")

    # --- Étape 2/3 : "Nbre joueurs" -> dialogue "dlg" (validation directe) ---
    if CONFIRMATION_MANUELLE:
        reponse2 = input(
            f"[bot] Étape 2/3 : cliquer 'Nbre joueurs' et sélectionner {nb_joueurs}. Confirmer ? (o/N) : "
        ).strip().lower()
        if reponse2 != "o":
            print("[bot] Annulé à l'étape 2 : piste ouverte, joueurs non configurés.")
            return {"succes": True, "piste": data.get("piste"), "nomJoueur": nom, "etape": "arrete_avant_nb_joueurs"}

    _cliquer(bouton_nb_joueurs)

    dialogue_nb = fenetre.child_window(auto_id="dlg", control_type="Window")
    _cliquer(dialogue_nb.child_window(title=nb_joueurs, control_type="Button"))
    print(f"[bot] {nb_joueurs} joueur(s) créé(s) (placeholders).")

    # --- Étape 3/3 : configuration de chaque joueur (clic + set_text) ---
    noms_appliques = []
    tarifs_appliques = {}
    if joueurs:
        if CONFIRMATION_MANUELLE:
            reponse3 = input(
                f"[bot] Étape 3/3 : configurer {len(joueurs)} joueur(s) "
                f"({', '.join(j.get('nom', '?') for j in joueurs)}). Confirmer ? (o/N) : "
            ).strip().lower()
            if reponse3 != "o":
                print("[bot] Annulé à l'étape 3 : joueurs laissés avec leur nom par défaut.")
                joueurs = []

        for index, info_joueur in enumerate(joueurs, start=1):
            nom_joueur = info_joueur.get("nom")
            if not nom_joueur:
                continue
            nom_defaut = f"joueur{index}"
            tarif_joueur = info_joueur.get("tarif", "1")
            try:
                _configurer_joueur(
                    fenetre,
                    index,
                    nom_defaut,
                    nom_joueur,
                    bumpers=info_joueur.get("bumpers", False),
                )
                noms_appliques.append(nom_joueur)

                try:
                    _appliquer_tarif_parties(fenetre, index, nom_defaut, nom_joueur, tarif_joueur)
                    tarifs_appliques[nom_joueur] = tarif_joueur
                except Exception as exc:
                    print(f"[bot] Échec application tarif {tarif_joueur!r} pour {nom_joueur!r} : {exc}")
            except Exception as exc:
                print(f"[bot] Échec configuration joueur {nom_joueur!r} : {exc}")

    return {
        "succes": True,
        "piste": data.get("piste"),
        "nomJoueur": nom,
        "joueurs": noms_appliques,
        "nbJoueurs": nb_joueurs,
        "tarifs": tarifs_appliques,
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
