// Paramètres Bowling - tarification par plage horaire (cf. demande Beer
// 2026-07-19). CRUD complet contre backend/src/routes/adminTarifsBowling.js.
//
// IMPORTANT : configuration uniquement pour l'instant - pas encore branché
// sur le calcul réel d'un prix de commande Bowling (paiement toujours
// simulé, cf. commentaire dans adminTarifsBowling.js). Cet écran prépare le
// terrain pour la Phase 3.
import { useEffect, useState } from "react";
import { api } from "../services/api";
import { IconPencil, IconPlus, IconTrash } from "./icons";

const JOURS = [
  { valeur: 1, label: "Lun" },
  { valeur: 2, label: "Mar" },
  { valeur: 3, label: "Mer" },
  { valeur: 4, label: "Jeu" },
  { valeur: 5, label: "Ven" },
  { valeur: 6, label: "Sam" },
  { valeur: 0, label: "Dim" },
];

const FORMULAIRE_VIDE = {
  label: "",
  heureDebut: "10:00",
  heureFin: "18:00",
  jours: [1, 2, 3, 4, 5, 6, 0],
  prixEuros: "5.00",
  actif: true,
};

function joursLabel(jours) {
  if (!jours || jours.length === 7) return "Tous les jours";
  return JOURS.filter((j) => jours.includes(j.valeur))
    .map((j) => j.label)
    .join(", ");
}

export default function ParametresBowlingTarifs() {
  const [tarifs, setTarifs] = useState(null);
  const [erreurChargement, setErreurChargement] = useState(null);
  const [formulaire, setFormulaire] = useState(FORMULAIRE_VIDE);
  const [idEnEdition, setIdEnEdition] = useState(null);
  const [soumission, setSoumission] = useState(false);
  const [erreurFormulaire, setErreurFormulaire] = useState(null);

  function charger() {
    api
      .getTarifsBowling()
      .then((res) => {
        setTarifs(res);
        setErreurChargement(null);
      })
      .catch((exc) => setErreurChargement(exc));
  }

  useEffect(() => {
    charger();
  }, []);

  function basculerJour(valeur) {
    setFormulaire((f) => ({
      ...f,
      jours: f.jours.includes(valeur) ? f.jours.filter((j) => j !== valeur) : [...f.jours, valeur],
    }));
  }

  function commencerEdition(tarif) {
    setIdEnEdition(tarif.id);
    setFormulaire({
      label: tarif.label,
      heureDebut: tarif.heureDebut,
      heureFin: tarif.heureFin,
      jours: tarif.jours,
      prixEuros: (tarif.prixParPartieCentimes / 100).toFixed(2),
      actif: tarif.actif,
    });
    setErreurFormulaire(null);
  }

  function annulerEdition() {
    setIdEnEdition(null);
    setFormulaire(FORMULAIRE_VIDE);
    setErreurFormulaire(null);
  }

  async function soumettre(e) {
    e.preventDefault();
    setErreurFormulaire(null);

    const prix = Math.round(Number(formulaire.prixEuros) * 100);
    if (!formulaire.label.trim()) return setErreurFormulaire("Le label est requis.");
    if (formulaire.jours.length === 0) return setErreurFormulaire("Sélectionne au moins un jour.");
    if (!Number.isFinite(prix) || prix < 0) return setErreurFormulaire("Prix invalide.");
    // heureFin peut être < heureDebut (plage à cheval sur minuit, ex:
    // 17:00 -> 02:00 pour "on ferme après minuit") - seule l'égalité stricte
    // est rejetée (plage de durée nulle/ambiguë). Cf. commentaire détaillé
    // dans backend/src/tarificationBowling.js pour la convention complète
    // (heureFin exclusive - donc deux plages qui s'enchaînent se configurent
    // avec la même heure ronde des deux côtés, ex: 13:00-17:00 / 17:00-02:00).
    if (formulaire.heureDebut === formulaire.heureFin) return setErreurFormulaire("L'heure de fin doit différer de l'heure de début.");

    const payload = {
      label: formulaire.label.trim(),
      heureDebut: formulaire.heureDebut,
      heureFin: formulaire.heureFin,
      jours: formulaire.jours,
      prixParPartieCentimes: prix,
      actif: formulaire.actif,
    };

    setSoumission(true);
    try {
      if (idEnEdition) {
        await api.modifierTarifBowling(idEnEdition, payload);
      } else {
        await api.creerTarifBowling(payload);
      }
      annulerEdition();
      charger();
    } catch (exc) {
      setErreurFormulaire(exc.corps?.details?.join(", ") || exc.message);
    } finally {
      setSoumission(false);
    }
  }

  async function supprimer(tarif) {
    if (!window.confirm(`Supprimer la plage « ${tarif.label} » ?`)) return;
    try {
      await api.supprimerTarifBowling(tarif.id);
      charger();
    } catch (exc) {
      window.alert(`Suppression impossible : ${exc.message}`);
    }
  }

  return (
    <>
      <div className="carte">
        <h2 style={{ fontSize: 15, marginTop: 0, marginBottom: 18 }}>
          {idEnEdition ? "Modifier la plage tarifaire" : "Ajouter une plage tarifaire"}
        </h2>

        <form onSubmit={soumettre}>
          <div className="formulaire-grille">
            <div className="champ-formulaire">
              <label htmlFor="label">Label</label>
              <input
                id="label"
                type="text"
                value={formulaire.label}
                onChange={(e) => setFormulaire((f) => ({ ...f, label: e.target.value }))}
                placeholder="Ex : Happy Hour"
              />
            </div>
            <div className="champ-formulaire">
              <label htmlFor="heureDebut">Heure de début</label>
              <input
                id="heureDebut"
                type="time"
                value={formulaire.heureDebut}
                onChange={(e) => setFormulaire((f) => ({ ...f, heureDebut: e.target.value }))}
              />
            </div>
            <div className="champ-formulaire">
              <label htmlFor="heureFin">Heure de fin</label>
              <input
                id="heureFin"
                type="time"
                value={formulaire.heureFin}
                onChange={(e) => setFormulaire((f) => ({ ...f, heureFin: e.target.value }))}
              />
            </div>
            <div className="champ-formulaire">
              <label htmlFor="prix">Prix / partie (€)</label>
              <input
                id="prix"
                type="number"
                min="0"
                step="0.10"
                value={formulaire.prixEuros}
                onChange={(e) => setFormulaire((f) => ({ ...f, prixEuros: e.target.value }))}
              />
            </div>
          </div>

          <p className="texte-aide-formulaire">
            Pour enchaîner deux plages sans trou, utilise la même heure ronde des deux côtés (ex : 13:00–17:00 puis
            17:00–02:00) — l'heure de fin n'est jamais incluse dans la plage. L'heure de fin peut être plus petite que
            l'heure de début pour une plage qui traverse minuit (ex : 17:00 → 02:00). Les jours sélectionnés sont ceux
            où la plage <em>commence</em>.
          </p>

          <div className="champ-formulaire" style={{ marginBottom: 18 }}>
            <label>Jours</label>
            <div className="jours-checkboxes">
              {JOURS.map((j) => (
                <label className="jour-case" key={j.valeur}>
                  <input
                    type="checkbox"
                    checked={formulaire.jours.includes(j.valeur)}
                    onChange={() => basculerJour(j.valeur)}
                  />
                  <span>{j.label}</span>
                </label>
              ))}
            </div>
          </div>

          <label className="checkbox-inline" style={{ marginBottom: 18 }}>
            <input
              type="checkbox"
              checked={formulaire.actif}
              onChange={(e) => setFormulaire((f) => ({ ...f, actif: e.target.checked }))}
            />
            Plage active
          </label>

          {erreurFormulaire && <p className="texte-erreur-formulaire">{erreurFormulaire}</p>}

          <div className="formulaire-actions">
            <button type="submit" className="bouton-primaire" disabled={soumission}>
              <IconPlus className="icone-bouton" />
              {idEnEdition ? "Enregistrer les modifications" : "Ajouter la plage"}
            </button>
            {idEnEdition && (
              <button type="button" className="bouton-secondaire" onClick={annulerEdition}>
                Annuler
              </button>
            )}
          </div>
        </form>
      </div>

      {erreurChargement && <div className="etat-erreur">Erreur de chargement : {erreurChargement.message}</div>}

      {tarifs && tarifs.length === 0 && (
        <div className="etat-vide">Aucune plage tarifaire configurée pour l'instant.</div>
      )}

      {tarifs && tarifs.length > 0 && (
        <table className="liste">
          <thead>
            <tr>
              <th>Label</th>
              <th>Jours</th>
              <th>Horaires</th>
              <th>Prix / partie</th>
              <th>Statut</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {tarifs.map((t) => (
              <tr key={t.id}>
                <td className="lien-numero">{t.label}</td>
                <td>{joursLabel(t.jours)}</td>
                <td>
                  {t.heureDebut} – {t.heureFin}
                </td>
                <td>{(t.prixParPartieCentimes / 100).toLocaleString("fr-FR", { style: "currency", currency: "EUR" })}</td>
                <td>{t.actif ? "Active" : "Inactive"}</td>
                <td>
                  <div className="actions-icones">
                    <button type="button" className="bouton-icone" onClick={() => commencerEdition(t)} title="Modifier">
                      <IconPencil />
                    </button>
                    <button type="button" className="bouton-icone danger" onClick={() => supprimer(t)} title="Supprimer">
                      <IconTrash />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
