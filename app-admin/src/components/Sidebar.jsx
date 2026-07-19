// Sidebar Back-Office : un module par bloc, dépliable en accordéon animé,
// avec un sous-menu "Commandes" / "Paramètres" (cf. demande Beer
// 2026-07-19). Le module correspondant à l'URL courante est déplié par
// défaut, plutôt que de partir toujours fermé et forcer un clic supplémentaire.
import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { MODULES } from "../config";
import { IconActivity, IconBar, IconBowling, IconChevron, IconKaraoke, IconQuiz } from "./icons";
import ThemeToggle from "./ThemeToggle";

const ICONES = {
  bowling: IconBowling,
  bar: IconBar,
  karaoke: IconKaraoke,
  quiz: IconQuiz,
};

export default function Sidebar() {
  const location = useLocation();
  const moduleActifCle = MODULES.find((m) => location.pathname.startsWith(`/${m.cle}`))?.cle;

  const [ouvert, setOuvert] = useState(() => new Set(moduleActifCle ? [moduleActifCle] : []));

  function basculer(cle) {
    setOuvert((precedent) => {
      const suivant = new Set(precedent);
      if (suivant.has(cle)) suivant.delete(cle);
      else suivant.add(cle);
      return suivant;
    });
  }

  return (
    <nav className="sidebar">
      <div className="sidebar-titre">
        <span className="sidebar-logo">BB</span>
        <div className="sidebar-titre-texte">
          Back-Office
          <small>Bornes Bowling</small>
        </div>
      </div>

      <div className="sidebar-nav-globale">
        <NavLink to="/statut" className={({ isActive }) => `sidebar-lien-global${isActive ? " actif" : ""}`}>
          <IconActivity className="sidebar-module-icone" />
          Statut système
        </NavLink>
      </div>

      <div className="sidebar-modules">
        {MODULES.map((module) => {
          const Icone = ICONES[module.cle];
          const estOuvert = ouvert.has(module.cle);
          const estModuleActif = module.cle === moduleActifCle;
          return (
            <div className="sidebar-module" key={module.cle}>
              <button
                type="button"
                className={`sidebar-module-bouton${estModuleActif ? " actif" : ""}`}
                onClick={() => basculer(module.cle)}
                aria-expanded={estOuvert}
              >
                <span className="sidebar-module-label">
                  <Icone className="sidebar-module-icone" />
                  {module.label}
                </span>
                <IconChevron className={`sidebar-chevron${estOuvert ? " ouvert" : ""}`} />
              </button>

              {/* Toujours monté (pas de rendu conditionnel) pour que
                  l'accordéon puisse s'animer via grid-template-rows - cf.
                  index.css. */}
              <div className={`sidebar-sousmenu-wrap${estOuvert ? " ouvert" : ""}`}>
                <div className="sidebar-sousmenu-inner">
                  <ul className="sidebar-sousmenu">
                    <li>
                      <NavLink
                        to={`/${module.cle}/commandes`}
                        className={({ isActive }) => (isActive ? "actif" : undefined)}
                      >
                        Commandes
                      </NavLink>
                    </li>
                    <li>
                      <NavLink
                        to={`/${module.cle}/parametres`}
                        className={({ isActive }) => (isActive ? "actif" : undefined)}
                      >
                        Paramètres
                      </NavLink>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="sidebar-pied">
        <ThemeToggle />
      </div>
    </nav>
  );
}
