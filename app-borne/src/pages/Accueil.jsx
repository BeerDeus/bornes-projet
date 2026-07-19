import { Link } from "react-router-dom";

export default function Accueil() {
  return (
    <div style={{ display: "flex", gap: 24, justifyContent: "center", marginTop: 60 }}>
      <Link to="/bar" style={styleCarte}>🍹 Bar</Link>
      <Link to="/bowling" style={styleCarte}>🎳 Bowling (test)</Link>
    </div>
  );
}

const styleCarte = {
  display: "flex", alignItems: "center", justifyContent: "center",
  width: 220, height: 160, borderRadius: 16, background: "#2563eb",
  color: "white", fontSize: 22, fontWeight: "bold", textDecoration: "none",
};
