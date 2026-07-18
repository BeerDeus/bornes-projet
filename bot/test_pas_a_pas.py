"""
Diagnostic pas-à-pas - Phase 1
=================================
Contourne complètement le backend/bot WebSocket : lance directement les
clics dans Conqueror, un par un, avec vérification explicite après chaque
étape (le script te dit s'il détecte que ça a marché, plutôt que de
supposer que ça a marché juste parce qu'aucune erreur n'a été levée).

But : trouver précisément où et pourquoi les clics automatisés échouent.

Usage (PC Conqueror, dans bot/ avec le venv activé) :
  python test_pas_a_pas.py

Répond Entrée à chaque pause, en vérifiant sur l'écran Conqueror ce qui est
annoncé avant de continuer.
"""

import time

from pywinauto import Application


def pause(message):
    input(f"\n[ÉTAPE] {message}\nAppuie sur Entrée pour continuer...")


def rapport(label, valeur):
    print(f"  -> {label} : {valeur}")


print("Connexion à Conqueror...")
app = Application(backend="uia").connect(title_re=".*Conqueror.*")
fenetre = app.top_window()
fenetre.set_focus()
time.sleep(0.5)
rapport("Fenêtre active", fenetre.window_text())

# --- Étape 1 : Référence + Sple Partie ---
pause("Sur le point de remplir 'Référence' avec 'TestDiag' puis cliquer 'Sple Partie'.")

champ_ref = fenetre.child_window(auto_id="RéférenceEntry", control_type="Edit")
champ_ref.set_text("TestDiag")
time.sleep(0.3)
rapport("Texte relu dans le champ Référence", champ_ref.window_text())

bouton_sple = fenetre.child_window(title="Sple Partie", control_type="Button")
rapport("Bouton 'Sple Partie' trouvé, existe", bouton_sple.exists())
bouton_sple.click_input()
time.sleep(1)

# Vérification : le bouton "Nbre joueurs" doit être visible (signe qu'on est
# bien passé sur l'écran LaneControl).
bouton_nb = fenetre.child_window(auto_id="btnNbre joueurs", control_type="Button")
rapport("Après clic 'Sple Partie', bouton 'Nbre joueurs' détecté", bouton_nb.exists())

if not bouton_nb.exists():
    print("\n>>> Le clic sur 'Sple Partie' n'a pas amené sur l'écran LaneControl. Arrêt.")
    raise SystemExit(1)

# --- Étape 2 : Nbre joueurs ---
pause("Écran LaneControl confirmé. Sur le point de cliquer 'Nbre joueurs'.")

bouton_nb.click_input()
time.sleep(1)

dialogue = fenetre.child_window(auto_id="dlg", control_type="Window")
rapport("Après clic 'Nbre joueurs', dialogue 'dlg' détecté", dialogue.exists())

if not dialogue.exists():
    print("\n>>> Le clic sur 'Nbre joueurs' n'a pas ouvert le dialogue. Arrêt.")
    print(">>> Regarde ce qui est affiché sur Conqueror actuellement et décris-le.")
    raise SystemExit(1)

# --- Étape 3 : sélection du nombre + OK ---
pause("Dialogue 'Nombre de joueurs' confirmé ouvert. Sur le point de cliquer '2' puis 'OK'.")

bouton_2 = dialogue.child_window(title="2", control_type="Button")
rapport("Bouton '2' trouvé, existe", bouton_2.exists())
bouton_2.click_input()
time.sleep(0.5)

bouton_ok = dialogue.child_window(auto_id="btnOK", control_type="Button")
rapport("Bouton 'OK' trouvé, existe", bouton_ok.exists())
bouton_ok.click_input()
time.sleep(1)

rapport("Dialogue 'dlg' toujours présent (devrait être False = fermé)", dialogue.exists())

joueur2 = fenetre.child_window(title="joueur2", control_type="Text")
rapport("'joueur2' détecté dans la liste (signe que le nombre a été appliqué)", joueur2.exists())

print("\nFin du diagnostic. Regarde l'état final sur Conqueror et compare avec les rapports ci-dessus.")
