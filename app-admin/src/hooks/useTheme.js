// Thème clair/sombre, persisté en localStorage - cf. demande Beer
// (2026-07-19) "possibilité de changer de thème clair à sombre". La clé
// "admin-theme" est lue en synchrone dans index.html (avant montage React)
// pour éviter un flash de thème au chargement - garder les deux en phase.
import { useEffect, useState } from "react";

const STORAGE_KEY = "admin-theme";

function themeInitial() {
  try {
    const enregistre = localStorage.getItem(STORAGE_KEY);
    if (enregistre === "clair" || enregistre === "sombre") return enregistre;
  } catch {
    /* localStorage indisponible */
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "sombre" : "clair";
}

export function useTheme() {
  const [theme, setTheme] = useState(themeInitial);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* localStorage indisponible - le thème reste actif pour la session en cours */
    }
  }, [theme]);

  function basculer() {
    setTheme((t) => (t === "sombre" ? "clair" : "sombre"));
  }

  return { theme, basculer };
}
