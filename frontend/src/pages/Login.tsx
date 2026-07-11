import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { GoogleLogin, GoogleOAuthProvider } from "@react-oauth/google";
import { useTranslation } from "react-i18next";
import { useAuth } from "../lib/auth/useAuth";
import { StatusBanner } from "../components/StatusBanner";
import "./Login.css";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

interface LocationState {
  from?: { pathname: string };
}

export function Login() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [error, setError] = useState<string | null>(null);
  const isSpanish = i18n.language.startsWith("es");

  const from = (location.state as LocationState | null)?.from?.pathname ?? "/";

  return (
    <div className="login-page">
      <button
        type="button"
        className="layout-lang login-lang"
        title={t("nav.language")}
        onClick={() => i18n.changeLanguage(isSpanish ? "en" : "es")}
      >
        {isSpanish ? "ES" : "EN"}
      </button>
      <div className="login-card">
        <span className="layout-brand-mark login-brand-mark">CT</span>
        <h1>{t("login.brand")}</h1>
        <p className="dashboard-subtitle">{t("login.subtitle")}</p>

        {error && <StatusBanner kind="error">{error}</StatusBanner>}

        {GOOGLE_CLIENT_ID ? (
          <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <div className="login-google-button">
              <GoogleLogin
                onSuccess={async (credentialResponse) => {
                  setError(null);
                  if (!credentialResponse.credential) {
                    setError(t("login.noCredential"));
                    return;
                  }
                  try {
                    await signIn(credentialResponse.credential);
                    navigate(from, { replace: true });
                  } catch {
                    setError(t("login.signInFailed"));
                  }
                }}
                onError={() => setError(t("login.signInFailed"))}
              />
            </div>
          </GoogleOAuthProvider>
        ) : (
          <StatusBanner kind="error">{t("login.notConfigured")}</StatusBanner>
        )}
      </div>
    </div>
  );
}
