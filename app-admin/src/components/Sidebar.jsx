// Sidebar façon admin WordPress : un module par bloc, dépliable en
// accordéon, avec un sous-menu "Commandes" / "Paramètres" (cf. demande Beer
// 2026-07-19). Le module correspondant à l'URL courante est déplié par
// défaut, plutôt que de partir toujours fermé et forcer un clic supplémentaire.
import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { MODULES } from "../config";

export default function Sidebar() {
  const location = useLocation();
  const modulePresentDansUrl = MODULES.find((m) => location.pathname.startsWith(`/${m.cle}`));

  const [ouvert, setOuvert] = useState(() => new Set(modulePresentDansUrl ? [modulePresentDansUrl.cle] : []));

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
        Back-Office
        <small>Bornes Bowling</small>
      </div>

      {MODULES.map((module) => {
        const estOuvert = ouvert.has(module.cle);
        const estModuleActif = location.pathname.startsWith(`/${module.cle}`);
        return (
          <div className="sidebar-module" key={module.cle}>
            <button
              type="button"
              className={`sidebar-module-bouton${estModuleActif ? " actif" : ""}`}
              onClick={() => basculer(module.cle)}
              aria-expanded={estOuvert}
            >
              {module.label}
              <span className={`sidebar-chevron${estOuvert ? " ouvert" : ""}`}>▶</span>
            </button>
            {estOuvert && (
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
            )}
          </div>
        );
      })}
    </nav>
  );
}
