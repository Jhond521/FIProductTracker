import { api } from "./client";
import type { User } from "./types";

const BASE = "/api/v1/internal/auth";

export const authApi = {
  me: () => api.get<User>(`${BASE}/me`),
  googleSignIn: (credential: string) => api.post<User>(`${BASE}/google`, { credential }),
  logout: () => api.post<void>(`${BASE}/logout`, undefined),
};
