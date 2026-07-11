import { Link, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../lib/auth/useAuth";
import "./Layout.css";

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { t, i18n } = useTranslation();
  const isDashboard = location.pathname === "/";
  const isSpanish = i18n.language.startsWith("es");

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="layout">
      <header className="layout-header">
        <Link to="/" className="layout-brand">
          <span className="layout-brand-mark">CT</span>
          <span className="layout-brand-text">{t("login.brand")}</span>
        </Link>
        <nav className="layout-nav">
          {!isDashboard && (
            <Link to="/" className="layout-nav-link">
              {t("nav.dashboard")}
            </Link>
          )}
          <button
            type="button"
            className="layout-lang"
            title={t("nav.language")}
            onClick={() => i18n.changeLanguage(isSpanish ? "en" : "es")}
          >
            {isSpanish ? "ES" : "EN"}
          </button>
          {user && (
            <div className="layout-user">
              {user.picture_url && (
                <img src={user.picture_url} alt="" className="layout-user-avatar" />
              )}
              <span className="layout-user-name" title={user.name}>
                {user.name}
              </span>
              <button className="layout-logout" onClick={handleLogout}>
                {t("nav.logout")}
              </button>
            </div>
          )}
        </nav>
      </header>
      <main className="layout-main">{children}</main>
    </div>
  );
}
