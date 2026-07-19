import { useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function Layout({ children }) {
  const location = useLocation();
  return (
    <div className="mise-en-page">
      <Sidebar />
      <main className="contenu">
        {/* key=pathname : force un remount à chaque changement de page pour
            rejouer l'animation d'apparition (cf. .page-anim, index.css) -
            sensation plus fluide qu'un contenu qui saute d'un état à l'autre
            sans transition. */}
        <div key={location.pathname} className="page-anim">
          {children}
        </div>
      </main>
    </div>
  );
}
