"""
Outil d'inspection Conqueror - Phase 1
=========================================
À exécuter SUR le PC Conqueror (dans le même venv que le bot), avec Conqueror
ouvert sur l'écran depuis lequel on veut piloter le bot (ex: écran d'accueil
ou liste des pistes).

Objectif : trouver le titre exact de la fenêtre Conqueror, puis lister tous
ses contrôles (boutons, champs de texte...) pour écrire les bons sélecteurs
dans conqueror_bot.py (fonction ouvrir_nouvelle_partie_reelle).

Usage :
  python inspect_conqueror.py

Copie-colle toute la sortie de la console et envoie-la : ça permet d'écrire
les sélecteurs sans avoir accès à l'écran directement.
"""

from pywinauto import Desktop

print("=== Fenêtres actuellement ouvertes ===\n")
fenetres = Desktop(backend="uia").windows()
for i, w in enumerate(fenetres):
    try:
        print(f"[{i}] titre={w.window_text()!r}  classe={w.friendly_class_name()}")
    except Exception as exc:
        print(f"[{i}] (erreur lecture: {exc})")

print()
choix = input(
    "Numéro de la fenêtre Conqueror ci-dessus "
    "(Entrée = recherche automatique du mot 'conqueror') : "
).strip()

if choix:
    cible = fenetres[int(choix)]
else:
    candidats = [w for w in fenetres if "conqueror" in w.window_text().lower()]
    if not candidats:
        print("\nAucune fenêtre contenant 'conqueror' trouvée dans le titre.")
        print("Relance le script et choisis le numéro de fenêtre manuellement dans la liste ci-dessus.")
        raise SystemExit(1)
    cible = candidats[0]

print(f"\n=== Arbre des contrôles de : {cible.window_text()!r} ===\n")
cible.print_control_identifiers()

print(
    "\n\nCopie tout ce qui précède (depuis '=== Arbre des contrôles') "
    "et envoie-le pour qu'on identifie les bons boutons/champs."
)
