import Sidebar from "./Sidebar";

export default function Layout({ children }) {
  return (
    <div className="mise-en-page">
      <Sidebar />
      <main className="contenu">{children}</main>
    </div>
  );
}
