import { Link, useLocation } from "react-router-dom";
import "./Layout.css";

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const isDashboard = location.pathname === "/";

  return (
    <div className="layout">
      <header className="layout-header">
        <Link to="/" className="layout-brand">
          <span className="layout-brand-mark">CT</span>
          <span>Credit Tracker</span>
        </Link>
        <nav className="layout-nav">
          {!isDashboard && (
            <Link to="/" className="layout-nav-link">
              ← Dashboard
            </Link>
          )}
          <span className="layout-lang" title="Language switching coming soon">
            EN
          </span>
        </nav>
      </header>
      <main className="layout-main">{children}</main>
    </div>
  );
}
