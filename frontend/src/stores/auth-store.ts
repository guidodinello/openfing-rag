import type { JwtToken } from "@/types/auth";
import { isJWTExpired } from "@/utils/jwt";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
    accessToken: JwtToken | null;
    isAuthenticated: boolean;
    rememberMe: boolean; // Track if user wants to stay logged in
}

interface AuthActions {
    setAccessToken: (
        accessToken: AuthState["accessToken"],
        rememberMe?: boolean,
    ) => void;
    getValidatedAccessToken: () => AuthState["accessToken"] | null;
    clearAuth: () => void;
}

const initialState = {
    accessToken: null,
    isAuthenticated: false,
    rememberMe: false,
} as const satisfies AuthState;

/**
 * Security model:
 * 1. Refresh token: HTTPOnly cookie (backend-managed, immune to XSS)
 * 2. Access token: In-memory by default (cleared on tab close)
 * 3. "Remember Me": Persists only a flag to trigger auto-refresh on reload
 *
 * Flow on page reload:
 * - If rememberMe=true: App automatically calls /refresh on mount
 * - If rememberMe=false: User must re-login
 *
 * This gives you the best of both worlds:
 * - No long-lived tokens in localStorage (secure)
 * - Users stay logged in across page refreshes (UX)
 */
export const useAuthStore = create<AuthState & AuthActions>()(
    persist(
        (set, get) => ({
            ...initialState,

            clearAuth: () => set(initialState),

            setAccessToken: (accessToken, rememberMe = false) => {
                set({
                    accessToken,
                    isAuthenticated: !!accessToken,
                    rememberMe,
                });
            },

            getValidatedAccessToken: () => {
                const { accessToken } = get();

                if (!accessToken || isJWTExpired(accessToken)) {
                    return null;
                }

                return accessToken;
            },
        }),
        {
            name: "auth-storage",
            partialize: (state) => ({ rememberMe: state.rememberMe }),
        },
    ),
);
