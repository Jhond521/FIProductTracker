import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth/useAuth";
import "./Layout.css";

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const isDashboard = location.pathname === "/";

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

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
          {user && (
            <div className="layout-user">
              {user.picture_url && (
                <img src={user.picture_url} alt="" className="layout-user-avatar" />
              )}
              <span className="layout-user-name">{user.name}</span>
              <button className="layout-logout" onClick={handleLogout}>
                Log out
              </button>
            </div>
          )}
        </nav>
      </header>
      <main className="layout-main">{children}</main>
    </div>
  );
}
