import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { GoogleLogin, GoogleOAuthProvider } from "@react-oauth/google";
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
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as LocationState | null)?.from?.pathname ?? "/";

  return (
    <div className="login-page">
      <div className="login-card">
        <span className="layout-brand-mark login-brand-mark">CT</span>
        <h1>Credit Tracker</h1>
        <p className="dashboard-subtitle">See the real cost of your credit cards.</p>

        {error && <StatusBanner kind="error">{error}</StatusBanner>}

        {GOOGLE_CLIENT_ID ? (
          <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <div className="login-google-button">
              <GoogleLogin
                onSuccess={async (credentialResponse) => {
                  setError(null);
                  if (!credentialResponse.credential) {
                    setError("Google didn't return a credential. Please try again.");
                    return;
                  }
                  try {
                    await signIn(credentialResponse.credential);
                    navigate(from, { replace: true });
                  } catch {
                    setError("Sign-in failed. Please try again.");
                  }
                }}
                onError={() => setError("Sign-in failed. Please try again.")}
              />
            </div>
          </GoogleOAuthProvider>
        ) : (
          <StatusBanner kind="error">
            Google sign-in isn't configured yet (missing VITE_GOOGLE_CLIENT_ID).
          </StatusBanner>
        )}
      </div>
    </div>
  );
}
