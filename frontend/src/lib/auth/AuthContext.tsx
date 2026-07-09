import { useEffect, useState, type ReactNode } from "react";
import { authApi } from "../../api/auth";
import { ApiError } from "../../api/client";
import type { User } from "../../api/types";
import { AuthContext } from "./context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    authApi
      .me()
      .then((current) => {
        if (!cancelled) setUser(current);
      })
      .catch((err) => {
        // A 401 here just means "not signed in yet" — not an error to surface.
        if (!cancelled && !(err instanceof ApiError && err.status === 401)) {
          console.error("Failed to load session", err);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function signIn(credential: string) {
    const current = await authApi.googleSignIn(credential);
    setUser(current);
  }

  async function logout() {
    await authApi.logout();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
