import { useTheme } from "../hooks/useTheme";
import { IconSun, IconMoon } from "./icons";

export default function ThemeToggle() {
  const { theme, basculer } = useTheme();
  const sombre = theme === "sombre";

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={basculer}
      aria-pressed={sombre}
      title={sombre ? "Passer en thème clair" : "Passer en thème sombre"}
    >
      <span className="theme-toggle-track">
        <span className="theme-toggle-thumb">
          {sombre ? <IconMoon className="theme-toggle-icone" /> : <IconSun className="theme-toggle-icone" />}
        </span>
      </span>
      <span className="theme-toggle-label">{sombre ? "Sombre" : "Clair"}</span>
    </button>
  );
}
