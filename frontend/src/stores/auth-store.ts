import type { JwtToken } from "@/types/auth";
import { isJWTExpired } from "@/utils/jwt";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
    accessToken: JwtToken | null;
    refreshToken: JwtToken | null;
    isAuthenticated: boolean;
}

interface AuthActions {
    setTokens: (
        accessToken: AuthState["accessToken"],
        refreshToken: AuthState["refreshToken"],
    ) => void;
    getValidatedAccessToken: () => AuthState["accessToken"] | null;
    clearAuth: () => void;
}

export const useAuthStore = create<AuthState & AuthActions>()(
    persist(
        (set, get) => ({
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,

            setTokens: (accessToken, refreshToken) => {
                set({
                    accessToken,
                    refreshToken,
                    isAuthenticated: true,
                });
            },

            getValidatedAccessToken: () => {
                const { accessToken } = get();

                if (!accessToken || isJWTExpired(accessToken)) {
                    return null;
                }

                return accessToken;
            },

            clearAuth: () => {
                set({
                    accessToken: null,
                    refreshToken: null,
                    isAuthenticated: false,
                });
            },
        }),
        {
            name: "auth-storage",
            partialize: (state) => ({ refreshToken: state.refreshToken }),
        },
    ),
);
